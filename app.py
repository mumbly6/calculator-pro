"""
SmartCalc Suite - Streamlit MVP (app.py)

Features:
- Multi-tab Budget Calculator (Personal, Business, Government)
- Add / Reset entries; persistent in session_state
- Reports (Plotly) that always render correctly in browser/mobile
- Currency conversion (forex-python) with graceful fallback
- Simple login form; optional admin email notification on user login
- Feedback form that emails admin (optional)
- Export as JSON / CSV
- Polished UI with CSS glow/animation
- Meant for deployment on Streamlit Cloud / Render / similar

Required Python packages:
pip install streamlit pandas plotly forex-python yagmail python-dotenv

IMPORTANT for email features:
- Set EMAIL_USER and EMAIL_PASS in Streamlit secrets or environment variables.
  On Streamlit Cloud: put them in App Secrets:
    [secrets.toml]
    EMAIL_USER = "youremail@example.com"
    EMAIL_PASS = "app-password-or-oauth-token"
    ADMIN_EMAIL = "youremail@example.com"

- If you don't set them, the app will work but email notifications will not be sent.

Run locally:
streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import io
import os

# Currency conversion helper (forex-python)
try:
    from forex_python.converter import CurrencyRates
    has_forex = True
    c_rates = CurrencyRates(force_decimal=False)
except Exception:
    has_forex = False

# Email sending helper (yagmail)
try:
    import yagmail
    has_yag = True
except Exception:
    has_yag = False

# ---------------------------
# App config and CSS styling
# ---------------------------
st.set_page_config(page_title="SmartCalc Suite — Budget Calculator", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for glow and styling
st.markdown(
    """
    <style>
    /* Background & container */
    .reportview-container {
        background: linear-gradient(180deg, #fbfbff 0%, #f7f9ff 100%);
    }
    .glow-card {
        box-shadow: 0 6px 18px rgba(79,70,229,0.12), 0 0 30px rgba(79,70,229,0.06);
        transition: transform .22s ease, box-shadow .22s ease;
        border-radius: 12px;
        padding: 18px;
        background: white;
    }
    .glow-card:hover { transform: translateY(-6px); box-shadow: 0 14px 40px rgba(79,70,229,0.18), 0 0 40px rgba(79,70,229,0.08); }

    .big-metric { font-size: 20px; font-weight:700; color:#374151; }
    .muted { color:#6b7280; }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg,#7c3aed,#6366f1);
        color: white;
        border-radius: 10px;
        padding: 8px 14px;
        box-shadow: 0 6px 20px rgba(99,102,241,0.18);
        transition: transform .15s ease;
    }
    .stButton>button:hover{ transform: translateY(-3px); }

    /* Input styling */
    .stTextInput>div>div>input, .stNumberInput>div>input {
        border-radius: 8px;
        padding: 10px;
    }

    /* Mobile spacing */
    @media (max-width: 640px) {
      .glow-card { padding: 12px; }
    }
    </style>
    """, unsafe_allow_html=True
)

# ---------------------------
# Helpers
# ---------------------------
def send_email(subject: str, body: str, to_address: str):
    """
    Sends email using yagmail if credentials are configured.
    - Expects secrets: EMAIL_USER, EMAIL_PASS
    Returns True on send attempt, False otherwise.
    """
    email_user = st.secrets.get("EMAIL_USER") if "EMAIL_USER" in st.secrets else os.environ.get("EMAIL_USER")
    email_pass = st.secrets.get("EMAIL_PASS") if "EMAIL_PASS" in st.secrets else os.environ.get("EMAIL_PASS")
    if not email_user or not email_pass or not has_yag:
        return False
    try:
        yag = yagmail.SMTP(email_user, email_pass)
        yag.send(to=to_address, subject=subject, contents=body)
        return True
    except Exception as e:
        st.error(f"Email send failed: {e}")
        return False

def init_session():
    """Initialize session_state containers"""
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "personal_entries" not in st.session_state:
        st.session_state.personal_entries = []
    if "business_entries" not in st.session_state:
        st.session_state.business_entries = []
    if "government_entries" not in st.session_state:
        st.session_state.government_entries = []
    if "currency" not in st.session_state:
        st.session_state.currency = "USD"

def to_dataframe(entries):
    """Convert list of dict entries to DataFrame safely"""
    if not entries:
        return pd.DataFrame(columns=["timestamp", "items", "total_income", "total_expense", "total_saving", "net"])
    return pd.DataFrame(entries)

def compute_totals_from_inputs(income_values, expense_values, saving_values):
    income_total = sum([float(x or 0) for x in income_values])
    expense_total = sum([float(x or 0) for x in expense_values])
    saving_total = sum([float(x or 0) for x in saving_values])
    net = income_total - expense_total - saving_total
    return income_total, expense_total, saving_total, net

def add_entry(storage_key, items_dict):
    """Append an entry dict into the appropriate session list"""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "items": items_dict,
        "total_income": items_dict.get("total_income", 0),
        "total_expense": items_dict.get("total_expense", 0),
        "total_saving": items_dict.get("total_saving", 0),
        "net": items_dict.get("net", 0),
    }
    st.session_state[storage_key].append(entry)

# Currency conversion wrapper
def convert_currency(amount: float, from_cur: str, to_cur: str):
    """
    Convert amount from from_cur to to_cur using forex-python when available.
    Returns converted value or None if conversion unavailable.
    """
    if not has_forex:
        return None
    try:
        return c_rates.convert(from_cur.upper(), to_cur.upper(), float(amount))
    except Exception:
        return None

# ---------------------------
# Initialize session state
# ---------------------------
init_session()

# ---------------------------
# Simple Authentication
# ---------------------------
def login_area():
    st.sidebar.markdown("### 🔒 Sign in")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Sign in"):
        # For MVP: simple check (replace with DB or OAuth later)
        # Accept any non-empty username; optional admin password for admin user
        if username.strip() == "":
            st.sidebar.error("Enter a username to continue.")
            return
        # Example admin check (improve for production)
        if username.lower() == "admin":
            # require password that matches secret admin password if set
            admin_pass = st.secrets.get("ADMIN_PASS") if "ADMIN_PASS" in st.secrets else os.environ.get("ADMIN_PASS")
            if admin_pass and password != admin_pass:
                st.sidebar.error("Invalid admin password.")
                return
        # Successful login
        st.session_state.auth = True
        st.session_state.user = username
        st.sidebar.success(f"Signed in as {username}")
        # Send admin notification (optional)
        admin_email = st.secrets.get("ADMIN_EMAIL") if "ADMIN_EMAIL" in st.secrets else os.environ.get("ADMIN_EMAIL")
        if admin_email:
            subject = f"[SmartCalc] New login: {username}"
            body = f"User '{username}' signed in at {datetime.utcnow().isoformat()} UTC.\n\nYou can disable notifications by removing ADMIN_EMAIL from secrets."
            send_email(subject, body, admin_email)

if not st.session_state.auth:
    # Welcome screen + login
    st.title("Welcome to SmartCalc Suite")
    st.write("Please sign in on the left sidebar to continue. If you don't want to sign in, press 'Continue as guest' below.")
    if st.button("Continue as guest"):
        st.session_state.auth = True
        st.session_state.user = "guest"
else:
    st.sidebar.markdown(f"### 👋 {st.session_state.user}")
    if st.sidebar.button("Sign out"):
        st.session_state.auth = False
        st.session_state.user = None
        st.experimental_rerun()
    # Quick export of stored entries
    if st.sidebar.button("Export all data (JSON)"):
        all_data = {
            "personal": st.session_state.personal_entries,
            "business": st.session_state.business_entries,
            "government": st.session_state.government_entries
        }
        st.download_button("Download data", json.dumps(all_data, indent=2), file_name="smartcalc_data.json", mime="application/json")

# call login area in sidebar
login_area()

# If still not authenticated, stop rendering the app
if not st.session_state.auth:
    st.stop()

# ---------------------------
# App Body - Multi Tab UI
# ---------------------------
st.markdown("<div class='glow-card'>", unsafe_allow_html=True)
st.header("📊 SmartCalc Suite — Budget Calculator (MVP)")
st.markdown("Multi-tab budgeting for Personal, Business, and Government use. Add entries, generate reports, convert currency, and collect feedback.")
st.markdown("</div>", unsafe_allow_html=True)

# Tab layout
tabs = st.tabs(["Personal", "Business", "Government", "Reports & Insights", "Currency", "Feedback"])

# ---------------------------
# Helper UI builders
# ---------------------------
def budget_panel(tab_label, storage_key, income_labels, expense_labels, saving_labels):
    """
    Renders a budget panel inside a tab container (call from a with tabs[X] block).
    storage_key: 'personal_entries'|'business_entries'|'government_entries'
    """
    st.subheader(f"{tab_label} Budget")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Income**")
        income_vals = []
        for lbl in income_labels:
            income_vals.append(st.number_input(f"{tab_label} — {lbl}", min_value=0.0, key=f"{storage_key}_inc_{lbl}", format="%.2f"))
    with col2:
        st.markdown("**Expenses**")
        expense_vals = []
        for lbl in expense_labels:
            expense_vals.append(st.number_input(f"{tab_label} — {lbl}", min_value=0.0, key=f"{storage_key}_exp_{lbl}", format="%.2f"))
    with col3:
        st.markdown("**Savings / Allocations**")
        saving_vals = []
        for lbl in saving_labels:
            saving_vals.append(st.number_input(f"{tab_label} — {lbl}", min_value=0.0, key=f"{storage_key}_sav_{lbl}", format="%.2f"))

    total_income, total_expense, total_saving, net = compute_totals_from_inputs(income_vals, expense_vals, saving_vals)
    st.markdown("---")
    st.write(f"**Totals — Income:** {total_income:.2f}  •  **Expenses:** {total_expense:.2f}  •  **Savings:** {total_saving:.2f}")
    st.metric("Net Balance", f"{net:.2f} {st.session_state.currency}")

    colA, colB = st.columns([1, 1])
    if colA.button(f"Add {tab_label} Entry"):
        items = {
            "income_breakdown": dict(zip(income_labels, income_vals)),
            "expense_breakdown": dict(zip(expense_labels, expense_vals)),
            "saving_breakdown": dict(zip(saving_labels, saving_vals)),
            "total_income": total_income,
            "total_expense": total_expense,
            "total_saving": total_saving,
            "net": net,
            "creator": st.session_state.user
        }
        add_entry(storage_key, items)
        st.success(f"{tab_label} entry added.")
    if colB.button(f"Reset {tab_label} Inputs"):
        # reset inputs by setting to 0 using session rerun trick
        for lbl in income_labels:
            st.session_state[f"{storage_key}_inc_{lbl}"] = 0.0
        for lbl in expense_labels:
            st.session_state[f"{storage_key}_exp_{lbl}"] = 0.0
        for lbl in saving_labels:
            st.session_state[f"{storage_key}_sav_{lbl}"] = 0.0
        st.experimental_rerun()

    # Show recent entries table
    st.markdown("**Recent Entries**")
    df = to_dataframe(st.session_state[storage_key])
    if not df.empty:
        st.dataframe(df[["timestamp", "total_income", "total_expense", "total_saving", "net"]].sort_values("timestamp", ascending=False).head(8))
        # download button for this set
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button(f"Download {tab_label} CSV", csv_bytes, file_name=f"{storage_key}.csv", mime="text/csv")
    else:
        st.info("No entries yet for this category.")

# ---------------------------
# PERSONAL Tab
# ---------------------------
with tabs[0]:
    budget_panel("Personal", "personal_entries",
                 income_labels=["Salary", "Investments", "Other"],
                 expense_labels=["Housing", "Food", "Transport"],
                 saving_labels=["Emergency", "Retirement", "Other"])

# ---------------------------
# BUSINESS Tab
# ---------------------------
with tabs[1]:
    budget_panel("Business", "business_entries",
                 income_labels=["Product Sales", "Service Income", "Other"],
                 expense_labels=["Salaries", "Inventory", "Marketing"],
                 saving_labels=["R&D", "Growth Fund", "Reserves"])

# ---------------------------
# GOVERNMENT Tab
# ---------------------------
with tabs[2]:
    budget_panel("Government", "government_entries",
                 income_labels=["Tax Revenue", "Grants", "Borrowing"],
                 expense_labels=["Education", "Healthcare", "Infrastructure"],
                 saving_labels=["Development", "Defense", "Reserves"])

# ---------------------------
# REPORTS & INSIGHTS Tab
# ---------------------------
with tabs[3]:
    st.subheader("Reports & Insights")
    # Prepare aggregated numbers
    def sum_net(lst): return sum((float(x.get("net") or 0) for x in lst))
    def sum_exp(lst): return sum((float(x.get("total_expense") or 0) for x in lst))
    def sum_sav(lst): return sum((float(x.get("total_saving") or 0) for x in lst))
    def sum_inc(lst): return sum((float(x.get("total_income") or 0) for x in lst))

    personal_df = to_dataframe(st.session_state.personal_entries)
    business_df = to_dataframe(st.session_state.business_entries)
    government_df = to_dataframe(st.session_state.government_entries)

    agg = pd.DataFrame({
        "category": ["Personal", "Business", "Government"],
        "income": [sum_inc(st.session_state.personal_entries), sum_inc(st.session_state.business_entries), sum_inc(st.session_state.government_entries)],
        "expense": [sum_exp(st.session_state.personal_entries), sum_exp(st.session_state.business_entries), sum_exp(st.session_state.government_entries)],
        "saving": [sum_sav(st.session_state.personal_entries), sum_sav(st.session_state.business_entries), sum_sav(st.session_state.government_entries)],
        "net": [sum_net(st.session_state.personal_entries), sum_net(st.session_state.business_entries), sum_net(st.session_state.government_entries)]
    })

    if agg[["income", "expense", "saving"]].sum(axis=1).sum() == 0:
        st.info("No data yet. Add entries in the Personal/Business/Government tabs and then generate reports.")
    else:
        st.markdown("### Overview")
        st.dataframe(agg.set_index("category"))

        col1, col2 = st.columns(2)
        with col1:
            fig_income = px.bar(agg, x="category", y="income", title="Total Income by Category", text_auto=".2s")
            st.plotly_chart(fig_income, use_container_width=True)
        with col2:
            fig_net = px.bar(agg, x="category", y="net", title="Net Balance by Category", text_auto=".2s")
            st.plotly_chart(fig_net, use_container_width=True)

        st.markdown("### Expense Breakdown (combined)")
        expense_long = agg.melt(id_vars="category", value_vars=["expense"], var_name="type", value_name="value")
        fig_exp = px.pie(expense_long, values="value", names="category", title="Expense Share Across Categories")
        st.plotly_chart(fig_exp, use_container_width=True)

    # Export combined data
    if st.button("Export All Data (JSON)"):
        all_data = {
            "personal": st.session_state.personal_entries,
            "business": st.session_state.business_entries,
            "government": st.session_state.government_entries
        }
        st.download_button("Download JSON", data=json.dumps(all_data, indent=2), file_name="smartcalc_all.json", mime="application/json")

# ---------------------------
# CURRENCY Tab
# ---------------------------
with tabs[4]:
    st.subheader("Currency Converter")
    st.write("Choose the base currency and target currency. If conversion service is unavailable the app will notify you.")
    colA, colB = st.columns(2)
    with colA:
        base = st.selectbox("Base currency", options=["USD", "KES", "EUR", "GBP", "INR", "JPY"], index=0)
        amount = st.number_input("Amount", min_value=0.0, value=0.0)
    with colB:
        target = st.selectbox("Target currency", options=["USD", "KES", "EUR", "GBP", "INR", "JPY"], index=1)
        if st.button("Convert"):
            if has_forex:
                try:
                    converted = convert_currency(amount, base, target)
                    if converted is None:
                        st.error("Currency service unavailable.")
                    else:
                        st.success(f"{amount:.2f} {base} = {converted:.2f} {target}")
                        st.session_state.currency = target
                except Exception as e:
                    st.error(f"Conversion failed: {e}")
            else:
                st.warning("The currency conversion library is not installed or internet access is blocked. Install 'forex-python' to enable conversions.")

# ---------------------------
# FEEDBACK Tab
# ---------------------------
with tabs[5]:
    st.subheader("Feedback & Suggestions")
    st.write("Send us suggestions or report bugs. We'll email them to the admin address (if configured).")
    feedback_name = st.text_input("Your name (optional)")
    feedback_email = st.text_input("Your email (optional)")
    feedback_text = st.text_area("Your feedback or suggestion")
    if st.button("Submit Feedback"):
        if not feedback_text.strip():
            st.warning("Please write a message before submitting.")
        else:
            admin_email = st.secrets.get("ADMIN_EMAIL") if "ADMIN_EMAIL" in st.secrets else os.environ.get("ADMIN_EMAIL")
            body = f"Feedback from SmartCalc Suite\n\nFrom: {feedback_name or 'anonymous'} ({feedback_email or 'no email provided'})\n\nMessage:\n{feedback_text}\n\nTime: {datetime.utcnow().isoformat()} UTC"
            if admin_email:
                sent = send_email("SmartCalc Feedback", body, admin_email)
                if sent:
                    st.success("Thanks! Your feedback was emailed to the admin.")
                else:
                    st.info("Feedback saved locally (email not configured).")
                    # store as a local "feedback" entry
                    if "feedback_list" not in st.session_state:
                        st.session_state.feedback_list = []
                    st.session_state.feedback_list.append({"name": feedback_name, "email": feedback_email, "text": feedback_text, "ts": datetime.utcnow().isoformat()})
            else:
                st.info("No admin email configured. Feedback saved locally.")
                if "feedback_list" not in st.session_state:
                    st.session_state.feedback_list = []
                st.session_state.feedback_list.append({"name": feedback_name, "email": feedback_email, "text": feedback_text, "ts": datetime.utcnow().isoformat()})

# ---------------------------
# Footer / tips
# ---------------------------
st.markdown("---")
st.caption("Tip: Deploy this file to Streamlit Cloud (https://streamlit.io/cloud) or Render for public access. Add EMAIL_USER, EMAIL_PASS, ADMIN_EMAIL, and ADMIN_PASS to your app secrets for email and admin features to work securely.")

# End
