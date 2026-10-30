"""
pull_bp_definitions.py
----------------------
Pulls business process definitions out of a Workday tenant and writes one file
per definition that BP Workflow Studio imports as-is.

  - Service ...... Core_Implementation_Service
  - Operation .... Get_Business_Process_Definitions (read only, nothing is written)
  - Output ....... <out>/<Business process> - <Definition>.csv, in the same
                   columns as a Workday definition export (Step, Order, If, Type,
                   Specify, Optional, Group, Additional Information, All, ..., Do Not Advance, Complete).
                   Studio's importer and path engine build the paths from it.

Run it:
  python pull_bp_definitions.py --bp "Supplier Invoice Event"          # that process's definitions
  python pull_bp_definitions.py --bp "Supplier Invoice Event" --default-only
  python pull_bp_definitions.py --all                                  # every definition in the tenant
  python pull_bp_definitions.py --bp "Supplier Invoice Event" --dry-run  # print the request, send nothing
  python pull_bp_definitions.py --from-json raw/definitions.json       # rebuild the files offline

Environment variables (put them in a .env next to this file; see .env.example):
  WD_SERVICES_HOST   e.g. impl-services1.wd12.myworkday.com (the services host, not the UI host)
  WD_TENANT          e.g. commitconsulting_dpt1
  WD_ISU_USERNAME    the Integration System User name (with or without @tenant)
  WD_ISU_PASSWORD    its password
  WD_WWS_VERSION     defaults to v47.0
  WD_WSDL            optional: a local WSDL file or URL to build the client from.
                     The request always goes to the endpoint built from
                     WD_SERVICES_HOST + WD_TENANT, never to the address inside the WSDL.
  WD_BP_TYPE_ID_TYPE defaults to Business_Process_Type: the ID type used to name the
                     business process in --bp. Confirm it on the first live run.

Use an implementation or sandbox tenant first.
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

SERVICE_NAME = "Core_Implementation_Service"
OPERATION = "Get_Business_Process_Definitions"

# Same columns, in the same order, as a Workday business process definition export
COLUMNS = ["Step", "Order", "If", "Type", "Specify", "Optional", "Group", "Additional Information",
           "All", "Run As User", "Routing Modifier", "Due Date", "Due Date Is Based On Effective Date",
           "Do Not Advance", "Complete", "Help Text"]


# ── Config ───────────────────────────────────────────────────────────────────

def env(name, default=None, required=True):
    val = os.environ.get(name, default)
    if required and not val:
        raise SystemExit(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return val


def ws_username(user, tenant):
    """WS-Security wants isu_name@tenant. Accept either form."""
    return user if user.lower().endswith("@" + tenant.lower()) else f"{user}@{tenant}"


def endpoint(host, tenant, version):
    return f"https://{host}/ccx/service/{tenant}/{SERVICE_NAME}/{version}"


# ── Client ───────────────────────────────────────────────────────────────────

def build_client(host, tenant, version, wsdl, user=None, password=None):
    """A zeep client whose requests go to this tenant's endpoint, whatever address the WSDL holds."""
    from zeep import Client, Settings
    from zeep.wsse.username import UsernameToken

    wsse = UsernameToken(ws_username(user, tenant), password) if user else None
    client = Client(wsdl=wsdl, wsse=wsse, settings=Settings(strict=False, xml_huge_tree=True))
    binding = next(name for name in client.wsdl.bindings if SERVICE_NAME in str(name))
    return client, client.create_service(binding, endpoint(host, tenant, version))


def build_request(bp=None, id_type="Business_Process_Type", default_only=False, page=1, count=100):
    criteria = {}
    if bp:
        criteria["Business_Process_Type_Reference"] = {"ID": [{"type": id_type, "_value_1": bp}]}
    if default_only:
        criteria["Default_Definition"] = True
    request = {
        "Response_Filter": {"Page": page, "Count": count},
        "Response_Group": {"Include_Reference": True,
                           "Include_Business_Process_Definition_Data": True,
                           "Exclude_Delivery_Event_Service_Configuration": True},
    }
    if criteria:
        request["Request_Criteria"] = criteria
    return request


def fetch_all(service, request, verbose=True):
    """Every page of definitions, as plain dicts."""
    from zeep.helpers import serialize_object

    out, page = [], 1
    while True:
        request["Response_Filter"]["Page"] = page
        resp = serialize_object(service.Get_Business_Process_Definitions(**request), dict)
        data = (resp.get("Response_Data") or {}).get("Business_Process_Definition") or []
        out.extend(data)
        results = resp.get("Response_Results") or {}
        total = int(results.get("Total_Pages") or 1)
        if verbose:
            print(f"[INFO] Page {page} of {total}: {len(data)} definition(s)")
        if page >= total:
            return out
        page += 1


# ── Mapping a definition to export rows ──────────────────────────────────────

def ref_name(ref):
    """The readable name Workday puts on a reference, falling back to its first ID."""
    if not ref:
        return ""
    if isinstance(ref, list):
        return "\n".join(filter(None, (ref_name(r) for r in ref)))
    if ref.get("Descriptor"):
        return ref["Descriptor"]
    ids = ref.get("ID") or []
    return str(ids[0].get("_value_1", "")) if ids else ""


def yes(flag):
    return "Yes" if flag else "No"


def restriction_text(step):
    """The Additional Information wording a definition export uses."""
    parts = []
    for rr in step.get("Routing_Restriction_Data") or []:
        excl = [label for key, label in (("Exclude_Initiator", "Initiator"), ("Exclude_Prior_Approvers", "Approvers"),
                                          ("Exclude_Latest_Reviser", "Latest Reviser"), ("Exclude_Event_Subject", "Event Subject"))
                if rr.get(key)]
        if excl:
            parts.append("Restriction: " + ", ".join(excl))
        alt = ref_name(rr.get("Alternate_Security_Group_Reference"))
        if alt:
            parts.append("Alternate: " + alt.replace("\n", ", "))
    return " ".join(parts)


def help_text(step):
    texts = [h.get("Help_Text_for_Workflow_Step") for h in step.get("Workflow_Step_Help_Text_Data") or []]
    plain = [re.sub(r"<[^>]+>", " ", str(t)) for t in texts if t]
    return "\n\n".join(re.sub(r"\s+", " ", t).strip() for t in plain)


def step_specify(step):
    for key in ("Task_Reference", "To_Do_Reference", "Checklist_Reference", "Event_Service_Reference"):
        if step.get(key):
            return ref_name(step[key])
    integ = step.get("Integration_Background_Process_Definition_Data") or {}
    return integ.get("Process_Description") or ""


def order_key(order):
    m = re.match(r"^([a-z]+)(\d*)$", str(order or "").strip().lower())
    if not m:
        return (999, 0, str(order))
    letters = 0
    for ch in m.group(1):
        letters = letters * 26 + (ord(ch) - 96)
    return (letters, int(m.group(2) or 0), "")


def definition_names(defn):
    data = defn.get("Business_Process_Definition_Data") or {}
    bp = ref_name(data.get("Business_Process_Type_Reference")) or "Business process"
    if data.get("Default_Definition"):
        name = "Default Definition"
    else:
        name = data.get("Rule_Based_Workflow_Definition_Name") or ref_name(defn.get("Business_Process_Definition_Reference")) or "Definition"
        name = re.sub(r"^" + re.escape(bp) + r"\s*[-:(]?\s*", "", name).rstrip(")") or name
    return bp, name


def definition_rows(defn):
    data = defn.get("Business_Process_Definition_Data") or {}
    bp, name = definition_names(defn)
    rows = [COLUMNS, [f"{bp} ({name}) step a - Initiation", "a", "", "Initiation", "", "No"] + [""] * (len(COLUMNS) - 6)]
    for step in sorted(data.get("Business_Process_Step_Data") or [], key=lambda s: order_key(s.get("Order"))):
        order = str(step.get("Order") or "").strip()
        if order.lower() == "a":
            continue
        stype = ref_name(step.get("Business_Process_Step_Type_Reference")) or "Action"
        conds = [ref_name(c.get("Condition_Rule_Reference")) for c in step.get("Entry_Condition_Data") or []]
        row = {
            "Step": f"{bp} ({name}) step {order} - {stype}",
            "Order": order,
            "If": "\n\n".join(c for c in conds if c),
            "Type": stype,
            "Specify": step_specify(step),
            "Optional": yes(step.get("Optional_Step")),
            "Group": ref_name(step.get("Security_Group_Reference")),
            "Additional Information": restriction_text(step),
            "All": "Yes" if step.get("Process_by_All_in_Role") else "",
            "Run As User": ref_name(step.get("Run_As_User_Reference")),
            "Routing Modifier": ref_name(step.get("Routing_Modifier_Reference")),
            "Due Date": ref_name(step.get("Due_Date_Calculated_Date_Reference")),
            "Due Date Is Based On Effective Date": "Yes" if step.get("Due_Date_Is_Based_On_Effective_Date") else "",
            "Do Not Advance": "Yes" if step.get("Do_Not_Advance") else "",
            "Complete": "Yes" if step.get("Completion_Step") else "",
            "Help Text": help_text(step),
        }
        rows.append([row[c] for c in COLUMNS])
    return bp, name, rows


def safe_filename(text):
    return re.sub(r"[^\w\- ()]+", "", text).strip()[:120] or "definition"


def write_outputs(definitions, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for defn in definitions:
        bp, name, rows = definition_rows(defn)
        path = out_dir / f"{safe_filename(bp)} - {safe_filename(name)}.csv"
        n = 2
        while path in written:
            path = out_dir / f"{safe_filename(bp)} - {safe_filename(name)} ({n}).csv"
            n += 1
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(rows)
        written.append(path)
        print(f"[OK]   {path.name}  ({len(rows) - 2} steps after initiation)")
    return written


def json_default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    return str(o)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv=None):
    p = argparse.ArgumentParser(description="Pull business process definitions for BP Workflow Studio (read only).")
    what = p.add_mutually_exclusive_group(required=True)
    what.add_argument("--bp", help='Business process type, e.g. "Supplier Invoice Event"')
    what.add_argument("--all", action="store_true", help="Every business process definition in the tenant")
    what.add_argument("--from-json", type=Path, help="Rebuild the files from a raw JSON pull, offline")
    p.add_argument("--default-only", action="store_true", help="Only Default Definitions")
    p.add_argument("--out", type=Path, default=Path("pulled"), help="Output folder (default: ./pulled)")
    p.add_argument("--raw", action="store_true", help="Also save the raw response as JSON (for checking and Phase 4)")
    p.add_argument("--count", type=int, default=100, help="Definitions per page (default 100)")
    p.add_argument("--dry-run", action="store_true", help="Print the SOAP request without sending it")
    args = p.parse_args(argv)

    if args.from_json:
        definitions = json.loads(args.from_json.read_text(encoding="utf-8"))
        write_outputs(definitions, args.out)
        return 0

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).with_name(".env"))
    except ImportError:
        pass

    host, tenant = env("WD_SERVICES_HOST"), env("WD_TENANT")
    version = env("WD_WWS_VERSION", "v47.0")
    wsdl = os.environ.get("WD_WSDL") or endpoint(host, tenant, version) + "?wsdl"
    id_type = env("WD_BP_TYPE_ID_TYPE", "Business_Process_Type")
    request = build_request(args.bp, id_type, args.default_only, count=args.count)

    print(f"[INFO] Tenant {tenant} on {host}, {SERVICE_NAME} {version}")
    print(f"[INFO] {OPERATION}: {('business process ' + repr(args.bp)) if args.bp else 'all business processes'}"
          f"{', Default Definitions only' if args.default_only else ''}")

    if args.dry_run:
        from lxml import etree
        client, service = build_client(host, tenant, version, wsdl)
        msg = client.create_message(service, OPERATION, **request)
        print(f"[DRY RUN] Would POST to {endpoint(host, tenant, version)}:")
        print(etree.tostring(msg, pretty_print=True).decode())
        return 0

    password = env("WD_ISU_PASSWORD")
    try:
        client, service = build_client(host, tenant, version, wsdl, env("WD_ISU_USERNAME"), password)
        definitions = fetch_all(service, request)
    except Exception as e:  # never echo the password back
        print(f"[ERROR] {type(e).__name__}: {str(e).replace(password, '***')}", file=sys.stderr)
        return 1

    if not definitions:
        print("[INFO] No definitions returned. Check the business process name and WD_BP_TYPE_ID_TYPE.")
        return 0
    if args.raw:
        args.out.mkdir(parents=True, exist_ok=True)
        raw = args.out / "raw_definitions.json"
        raw.write_text(json.dumps(definitions, indent=1, default=json_default), encoding="utf-8")
        print(f"[OK]   {raw.name} (raw response)")
    write_outputs(definitions, args.out)
    print(f"[DONE] {len(definitions)} definition(s). Import the .csv files in BP Workflow Studio (Home, Choose files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
