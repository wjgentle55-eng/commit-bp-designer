# Pull business process definitions from Workday

A read-only command-line tool that pulls business process definitions from a
Workday tenant into files BP Workflow Studio imports. It calls
`Get_Business_Process_Definitions` on `Core_Implementation_Service` and never
writes to the tenant.

Each definition becomes one `.csv` in the same columns as a Workday definition
export (Step, Order, If, Type, Specify, Optional, Group, Additional
Information, All, Run As User, Routing Modifier, Due Date, Do Not Advance, Complete, plus Help
Text). Studio imports it like an export: entry conditions become step
conditions, shared conditions become paths, and Complete = Yes becomes the
Document approved block.

## Setup

```bash
cd tools/wd_pull
python -m venv .venv
```

Activate it (`source .venv/bin/activate` on Mac, `.venv\Scripts\Activate.ps1` on Windows), then:

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with an Integration System User for an implementation or
sandbox tenant. The ISU needs Get access to business process definitions
(the Business Process Administration domain, or your tenant's equivalent).
`.env` and everything the tool pulls are gitignored.

## Run it

```bash
python pull_bp_definitions.py --bp "Supplier Invoice Event" --dry-run
```

Prints the exact SOAP request without sending it. Do this first.

```bash
python pull_bp_definitions.py --bp "Supplier Invoice Event" --raw
```

Pulls every definition of that process into `./pulled`. `--raw` also saves
the response as `raw_definitions.json`.

| Option | What it does |
| --- | --- |
| `--bp "<name>"` | One business process type |
| `--all` | Every definition in the tenant (mass pull) |
| `--default-only` | Only Default Definitions |
| `--out <folder>` | Where files go (default `./pulled`) |
| `--raw` | Also save the raw response as JSON |
| `--from-json <file>` | Rebuild the `.csv` files from a saved raw pull, offline |
| `--dry-run` | Show the request, send nothing |

## Into Studio

On Studio's Home page, open the client's folder, then drop the `.csv` files
(or use Choose a file). Several files at once are each saved as a definition
in that client's folder, filed by business process.

## Confirm on the first live run

These come from the WSDL schema and haven't been tested against a tenant yet:

1. **The business process ID type.** `--bp` sends the name with ID type
   `Business_Process_Type`. If nothing comes back, try `--all --default-only`
   with `--raw`, look up the `ID` types on `Business_Process_Type_Reference`
   in the raw file, and set `WD_BP_TYPE_ID_TYPE`.
2. **Readable names.** Conditions, groups, tasks and due dates use each
   reference's `Descriptor`. If a column shows IDs instead of names, check the
   raw file.
3. **Workday owned conditions.** A definition export marks them "(Workday
   Owned)"; it isn't yet known whether the web service does. Until it is, they
   come in as ordinary conditions. Phase 4 reads condition rules directly.
4. **API version.** v47.0 is the default; some tenants support an older
   version only. Set `WD_WWS_VERSION` if the WSDL fetch fails.
