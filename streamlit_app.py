"""
BP Workflow Studio on Streamlit.

  streamlit run streamlit_app.py

Studio (index.html) fills the page. The sidebar's Pull from Workday panel calls
Get_Business_Process_Definitions (read only) with the ISU credentials entered
there, and hands the definitions to Studio, which builds them into blocks and
paths and saves them into the named client folder.

Streamlit Community Cloud: deploy this repo with streamlit_app.py as the main
file. Optional secret (App settings > Secrets):
  STUDIO_ACCESS_CODE = "a team code"   # asked for before a pull
The password is used for one pull and cleared; it is never stored or logged.
Clients, folders and definitions are saved in each person's browser.
"""

import hmac
import json
import re
import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools" / "wd_pull"))
import studio_server as srv  # noqa: E402  (its run_pull does the validated, read-only call)

st.set_page_config(page_title="BP Workflow Studio", page_icon=str(ROOT / "assets" / "commit-icon.png"), layout="wide",
                   initial_sidebar_state="expanded")
st.markdown("""<style>
  header[data-testid="stHeader"]{background:transparent}
  .block-container{padding:0.5rem 0.75rem 0 0.75rem;max-width:100%}
  footer{visibility:hidden}
</style>""", unsafe_allow_html=True)


@st.cache_data
def studio_html():
    return (ROOT / "index.html").read_text(encoding="utf-8")


@st.cache_data
def business_processes():
    """The business process names Studio itself offers (BP_TASKS in index.html)."""
    m = re.search(r"^const BP_TASKS = (\{.*\});\s*$", studio_html(), re.M)
    try:
        names = set(json.loads(m.group(1))) if m else set()
    except ValueError:
        names = set()
    return sorted(names | {"Supplier Invoice Event", "Supplier Change Event"})


def access_code():
    try:
        return str(st.secrets.get("STUDIO_ACCESS_CODE", "") or "")
    except Exception:  # no secrets file when run locally
        return ""


def pass_key():
    return f"pl_pass_{st.session_state.get('pass_n', 0)}"


def do_pull():
    """Runs on Pull: one read-only call, then the password is cleared."""
    s = st.session_state
    code = access_code()
    try:
        if code and not hmac.compare_digest(code.encode(), (s.get("pl_code") or "").encode()):
            raise srv.PullError("That access code isn't right.")
        every = s.get("pl_all", False)
        if not every and not s.get("pl_bp"):
            raise srv.PullError("Pick a business process, or tick All business processes.")
        result = srv.run_pull({"host": s.get("pl_host"), "tenant": s.get("pl_tenant"), "username": s.get("pl_user"),
                               "password": s.get(pass_key()), "bp": "" if every else s.get("pl_bp"),
                               "defaultOnly": s.get("pl_default", True), "version": s.get("pl_ver") or "v47.0",
                               "idType": s.get("pl_idt") or "Business_Process_Type"})
        if not result["definitions"]:
            raise srv.PullError(f"No definitions came back for {s.get('pl_bp') or 'this tenant'}. "
                                "Check the name, or the ID type under Advanced.")
        s.pulled = {"id": uuid.uuid4().hex, "client": (s.get("pl_client") or "").strip(), **result}
        s.pull_msg = ("ok", f"Pulled {len(result['definitions'])} definition(s) from {result['tenant']}.")
    except srv.PullError as e:
        s.pull_msg = ("error", str(e))
    except Exception as e:  # never show the request: it holds the password
        s.pull_msg = ("error", f"The pull failed unexpectedly ({type(e).__name__}).")
    finally:
        # A fresh, empty password field after every pull (the old value is dropped from the session too)
        s.pop(pass_key(), None)
        s.pass_n = s.get("pass_n", 0) + 1


with st.sidebar:
    st.subheader("Pull from Workday")
    st.caption("Read only: nothing is written to the tenant. The password is used for this pull and isn't saved.")
    # A form sends every field together on Pull, so nothing typed is lost to a rerun
    with st.form("pull"):
        if access_code():
            st.text_input("Studio access code", type="password", key="pl_code")
        st.text_input("Services host", key="pl_host", placeholder="impl-services1.wd12.myworkday.com")
        st.text_input("Tenant", key="pl_tenant", placeholder="e.g. commitconsulting_dpt1")
        st.text_input("ISU username", key="pl_user")
        st.text_input("ISU password", type="password", key=pass_key())
        st.selectbox("Business process", business_processes(), index=None, key="pl_bp",
                     placeholder="Start typing, e.g. Supplier Invoice Event")
        st.checkbox("All business processes (mass pull, ignores the one above)", key="pl_all")
        st.checkbox("Default Definitions only", value=True, key="pl_default")
        st.text_input("Save into client", key="pl_client", placeholder="e.g. Aprio (blank = No client)")
        with st.expander("Advanced"):
            st.text_input("Web service version", value="v47.0", key="pl_ver")
            st.text_input("Business process ID type", value="Business_Process_Type", key="pl_idt")
        st.form_submit_button("Pull definitions", type="primary", on_click=do_pull, width="stretch")
    if "pull_msg" in st.session_state:
        kind, text = st.session_state.pull_msg
        (st.success if kind == "ok" else st.error)(text)

# Studio, with the latest pull handed to it. It imports a pull once (by id), so reruns don't duplicate it.
embed = {"host": "streamlit", "pulled": st.session_state.get("pulled")}
payload = json.dumps(embed).replace("<", "\\u003c")  # pulled names can't close the script or open markup
page = studio_html().replace("</head>", f"<script>window.__STUDIO_EMBED__ = {payload};</script>\n</head>", 1)
st.iframe(page, height=960)
