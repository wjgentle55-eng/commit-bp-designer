"""
studio_server.py
----------------
Runs BP Workflow Studio on http://localhost:8765 with a "Pull from Workday"
helper behind it. The page sends the tenant, ISU credentials and business
process; this helper calls Get_Business_Process_Definitions (read only) and
returns the definitions in the export's columns, which Studio builds into
blocks and paths.

Run it:
  python studio_server.py            # then open http://localhost:8765
  python studio_server.py --port 9000

Why a helper: browsers block pages from calling Workday's SOAP services, and a
password should not live in a static page. This helper listens on 127.0.0.1
only, takes credentials per request, keeps nothing on disk and never logs the
password. It only talks to *.myworkday.com / *.workday.com services hosts.

Optional environment variables:
  WD_WSDL   a local WSDL file or URL to build clients from, instead of fetching
            <services host>/ccx/service/<tenant>/Core_Implementation_Service/<version>?wsdl
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pull_bp_definitions as pull  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]  # the repo: index.html, assets/, designs/
HOST_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*\.(myworkday|workday)\.com$", re.I)
TENANT_RE = re.compile(r"^[A-Za-z0-9_\-]{1,80}$")
VERSION_RE = re.compile(r"^v\d{1,3}\.\d{1,2}$")
ID_TYPE_RE = re.compile(r"^[A-Za-z_]{1,80}$")

# Parsing the WSDL is the slow part, so one zeep client per WSDL is kept and reused.
# Credentials differ per request, so each call sets them under that client's lock.
_clients, _clients_lock = {}, threading.Lock()


class PullError(Exception):
    """A problem worth showing the person as-is."""


def _client_for(wsdl):
    with _clients_lock:
        if wsdl not in _clients:
            from zeep import Client, Settings
            client = Client(wsdl=wsdl, settings=Settings(strict=False, xml_huge_tree=True))
            binding = next(name for name in client.wsdl.bindings if pull.SERVICE_NAME in str(name))
            _clients[wsdl] = (client, binding, threading.Lock())
        return _clients[wsdl]


def run_pull(params):
    """Validate the page's request, call Workday, return {definitions:[{bp, name, rows}]}."""
    host = str(params.get("host") or "").strip().lower()
    tenant = str(params.get("tenant") or "").strip()
    user = str(params.get("username") or "").strip()
    password = str(params.get("password") or "")
    version = str(params.get("version") or "v47.0").strip()
    id_type = str(params.get("idType") or "Business_Process_Type").strip()
    bp = (str(params.get("bp") or "").strip()) or None
    default_only = bool(params.get("defaultOnly"))

    if not HOST_RE.match(host):
        raise PullError("The services host should look like impl-services1.wd12.myworkday.com.")
    if not TENANT_RE.match(tenant):
        raise PullError("The tenant should be the tenant ID only, e.g. commitconsulting_dpt1.")
    if not user or not password:
        raise PullError("Enter the ISU username and password.")
    if not VERSION_RE.match(version):
        raise PullError("The web service version should look like v47.0.")
    if not ID_TYPE_RE.match(id_type):
        raise PullError("The business process ID type should be a single word, e.g. Business_Process_Type.")

    from zeep.wsse.username import UsernameToken
    from zeep.exceptions import Fault, TransportError
    import requests

    wsdl = os.environ.get("WD_WSDL") or pull.endpoint(host, tenant, version) + "?wsdl"
    try:
        client, binding, lock = _client_for(wsdl)
    except requests.exceptions.RequestException:
        raise PullError(f"Couldn't reach {host}. Check the services host and your connection.")
    except Exception as e:
        raise PullError(f"Couldn't load the web service description for {tenant} ({type(e).__name__}). "
                        f"Check the tenant ID and version {version}.")

    request = pull.build_request(bp, id_type, default_only)
    try:
        with lock:
            client.wsse = UsernameToken(pull.ws_username(user, tenant), password)
            try:
                service = client.create_service(binding, pull.endpoint(host, tenant, version))
                definitions = pull.fetch_all(service, request, verbose=False)
            finally:
                client.wsse = None
    except Fault as f:
        msg = (f.message or "").replace(password, "***")
        if re.search(r"invalid username or password|authentication", msg, re.I):
            raise PullError("Workday rejected the ISU username or password.")
        raise PullError(f"Workday returned an error: {msg}")
    except TransportError as t:
        raise PullError(f"Workday answered HTTP {t.status_code}. Check the tenant, version and ISU access.")
    except requests.exceptions.RequestException:
        raise PullError(f"Couldn't reach {host}. Check the services host and your connection.")

    out = []
    for defn in definitions:
        name_bp, name, rows = pull.definition_rows(defn)
        out.append({"bp": name_bp, "name": name, "rows": rows})
    return {"definitions": out, "tenant": tenant}


class Handler(BaseHTTPRequestHandler):
    server_version = "BPStudio/1"

    def log_message(self, fmt, *args):  # request lines only; bodies (and passwords) are never logged
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _same_origin(self):
        origin = self.headers.get("Origin")
        port = self.server.server_address[1]
        return origin in (None, f"http://localhost:{port}", f"http://127.0.0.1:{port}")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            return self._send(200, {"ok": True, "helper": "bp-studio-pull", "version": 1})
        target = (ROOT / ("index.html" if path in ("", "/") else path.lstrip("/"))).resolve()
        # Only the page and its assets: nothing outside the repo, no dotfiles, nothing under tools/ (pulled data, .env)
        parts = target.relative_to(ROOT).parts if ROOT in target.parents else None
        if not parts or parts[0] == "tools" or any(p.startswith(".") for p in parts) or not target.is_file():
            return self._send(404, {"error": "Not found"})
        self._send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or "application/octet-stream")

    def do_POST(self):
        if self.path != "/api/pull":
            return self._send(404, {"error": "Not found"})
        if not self._same_origin() or "application/json" not in (self.headers.get("Content-Type") or ""):
            return self._send(403, {"error": "Requests are accepted from this Studio page only."})
        try:
            length = min(int(self.headers.get("Content-Length") or 0), 64_000)
            params = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, run_pull(params))
        except PullError as e:
            self._send(400, {"error": str(e)})
        except Exception as e:  # unexpected: name the kind, never the request (it holds the password)
            self._send(500, {"error": f"The pull failed unexpectedly ({type(e).__name__}). Try the command-line tool with --raw for details."})


def main(argv=None):
    p = argparse.ArgumentParser(description="Run BP Workflow Studio with the Pull from Workday helper.")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args(argv)
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"BP Workflow Studio is running at http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
