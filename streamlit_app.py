# streamlit_app.py
# SmartCalc Suite — polished, corrected, full app
# Run: py -m streamlit run streamlit_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import random
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

# Optional Lottie: try import; if not available we'll implement a safe fallback
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except Exception:
    LOTTIE_AVAILABLE = False

# Helper to load Lottie JSON from URL (returns dict or None)
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

# Example Lottie URLs (replace any you prefer)
LOTTIE_HOME_URL = "https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json"  # money growth
LOTTIE_CHART_URL = "https://assets2.lottiefiles.com/private_files/lf30_editor_z4q6lx8l.json"  # charts
LOTTIE_LOGIN_URL = "https://assets10.lottiefiles.com/packages/lf20_5ngs2ksb.json"
LOTTIE_AUDIT_URL = "https://assets9.lottiefiles.com/packages/lf20_bhw1ul4g.json"
LOTTIE_LOGOUT_URL = "https://assets2.lottiefiles.com/private_files/lf30_editor_hx6bn7vg.json"

lottie_home = load_lottieurl(LOTTIE_HOME_URL)
lottie_chart = load_lottieurl(LOTTIE_CHART_URL)
lottie_login = load_lottieurl(LOTTIE_LOGIN_URL)
lottie_audit = load_lottieurl(LOTTIE_AUDIT_URL)
lottie_logout = load_lottieurl(LOTTIE_LOGOUT_URL)

# -------------------------
# Styling: glow, fonts, animations
# -------------------------
st.set_page_config(page_title="SmartCalc Suite", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
      html,body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #f8fafc, #eef2ff); }
      .hero { padding: 20px; border-radius: 12px; background: linear-gradient(180deg, rgba(99,102,241,0.06), rgba(147,51,234,0.03)); box-shadow: 0 10px 30px rgba(99,102,241,0.06); }
      .glow { box-shadow: 0 8px 30px rgba(99,102,241,0.12); border-radius: 12px; padding: 12px; background: white; }
      .primary { background: linear-gradient(90deg,#7c3aed,#6366f1); color: white; padding: 8px 12px; border-radius: 10px; border: none; cursor: pointer; }
      .primary:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(99,102,241,0.18); }
      .muted { color: #6b7280; }
      .counter { font-weight:800; color:#6d28d9; font-size:22px; transition: all .6s; }
      /* nicer metrics */
      .stMetricValue { font-weight:800 !important; color:#6d28d9 !important; }
      @media (max-width: 640px) {
        .hero { padding: 12px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Session state init
# -------------------------
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
if "audits" not in st.session_state:
    st.session_state.audits = []
if "feedback_list" not in st.session_state:
    st.session_state.feedback_list = []
if "currency" not in st.session_state:
    st.session_state.currency = "USD"
if "networth" not in st.session_state:
    st.session_state.networth = None

# -------------------------
# Email helper (safe, non-fatal)
# -------------------------
def send_admin_email(subject: str, body: str) -> bool:
    """Attempt to send email using SMTP credentials stored in secrets or env vars.
    Returns True if send attempted successfully, False otherwise."""
    try:
        email_user = None
        email_pass = None
        admin_mail = None
        # Prefer Streamlit secrets if available
        try:
            if "EMAIL_USER" in st.secrets:
                email_user = st.secrets["EMAIL_USER"]
            if "EMAIL_PASS" in st.secrets:
                email_pass = st.secrets["EMAIL_PASS"]
            if "ADMIN_EMAIL" in st.secrets:
                admin_mail = st.secrets["ADMIN_EMAIL"]
        except Exception:
            # st.secrets may raise if not set, fallback to env
            pass
        if not email_user:
            email_user = os.environ.get("EMAIL_USER")
        if not email_pass:
            email_pass = os.environ.get("EMAIL_PASS")
        if not admin_mail:
            admin_mail = os.environ.get("ADMIN_EMAIL")
        if not (email_user and email_pass and admin_mail):
            return False
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = email_user
        msg["To"] = admin_mail
        msg.set_content(body)
        # send via Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(email_user, email_pass)
            smtp.send_message(msg)
        return True
    except Exception as e:
        # don't crash the app if email fails, but log error locally
        if "email_errors" not in st.session_state:
            st.session_state.email_errors = []
        st.session_state.email_errors.append(str(e))
        return False

# -------------------------
# Login / Logout / Tips
# -------------------------
def login_sidebar():
    st.sidebar.header("Account")
    if not st.session_state.auth:
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")
        if st.sidebar.button("Sign in"):
            if username.strip() == "":
                st.sidebar.error("Enter a username to continue")
            else:
                # If ADMIN_PASS is configured, enforce for admin username
                admin_pass = None
                try:
                    if "ADMIN_PASS" in st.secrets:
                        admin_pass = st.secrets["ADMIN_PASS"]
                except Exception:
                    admin_pass = os.environ.get("ADMIN_PASS")
                if username.lower() == "admin" and admin_pass and password != admin_pass:
                    st.sidebar.error("Invalid admin password")
                else:
                    st.session_state.auth = True
                    st.session_state.user = username
                    st.sidebar.success(f"Signed in as {username}")
                    # send a short notification
                    send_admin_email("SmartCalc login", f"User {username} signed in at {datetime.utcnow().isoformat()} UTC")
        if st.sidebar.button("Continue as guest"):
            st.session_state.auth = True
            st.session_state.user = "guest"
            st.sidebar.success("Continuing as guest")
    else:
        st.sidebar.markdown(f"**Signed in as:** {st.session_state.user}")
        if st.sidebar.button("Sign out"):
            # give a tip on sign out
            tip = generate_financial_tip()
            st.sidebar.success("Signed out. Tip: " + tip)
            st.session_state.auth = False
            st.session_state.user = None
            st.experimental_rerun()

login_sidebar()
if not st.session_state.auth:
    st.stop()

# -------------------------
# Small helpers for entries and totals
# -------------------------
def add_budget_entry(category_key: str, income_map: dict, expense_map: dict, saving_map: dict):
    total_income = sum(float(v or 0) for v in income_map.values())
    total_expense = sum(float(v or 0) for v in expense_map.values())
    total_saving = sum(float(v or 0) for v in saving_map.values())
    net = total_income - total_expense - total_saving
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "income": income_map,
        "expense": expense_map,
        "saving": saving_map,
        "total_income": total_income,
        "total_expense": total_expense,
        "total_saving": total_saving,
        "net": net,
        "user": st.session_state.user,
    }
    if category_key == "personal":
        st.session_state.personal_entries.append(entry)
    elif category_key == "business":
        st.session_state.business_entries.append(entry)
    elif category_key == "government":
        st.session_state.government_entries.append(entry)

def df_from_entries(entries):
    if not entries:
        return pd.DataFrame(columns=["timestamp","total_income","total_expense","total_saving","net","user"])
    df = pd.DataFrame(entries)
    # keep key columns for display
    return df[["timestamp","total_income","total_expense","total_saving","net","user"]]

def generate_financial_tip():
    tips = [
        "Automate 10% of your income to savings — small habits compound.",
        "Prioritize reducing high-interest debt before new investments.",
        "Keep an emergency fund for at least 3 months' expenses.",
        "Diversify: combine safe bonds with a portion in equities.",
        "Track subscriptions — recurring small costs add up."
    ]
    return random.choice(tips)

# -------------------------
# Hero / Header
# -------------------------
def hero():
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown("<div class='hero'>", unsafe_allow_html=True)
        st.markdown("<h1 style='margin:0 0 6px 0'>SmartCalc Suite — Elite Budget & Audit</h1>", unsafe_allow_html=True)
        st.markdown("<div class='muted'>Multi-purpose budgeting, polished charts, net-worth comparisons, and civic audit tools.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        if LOTTIE_AVAILABLE and lottie_home:
            try:
                st_lottie(lottie_home, height=140, key="home_lottie")
            except Exception:
                pass
        else:
            # fallback: small metric box
            total_net = sum(e["net"] for e in (st.session_state.personal_entries + st.session_state.business_entries + st.session_state.government_entries))
            st.metric("Total Net (all)", f"${total_net:,.2f}")

hero()

# -------------------------
# Tabs / Main UI
# -------------------------
tabs = st.tabs(["Budget", "Reports", "Net Worth", "Gov Audit", "Feedback", "Settings"])

# ---------- BUDGET TAB ----------
with tabs[0]:
    st.header("Budget — Personal / Business / Government (Add entries below)")
    # Use forms for each category to avoid accidental reruns
    p_col, b_col, g_col = st.columns(3)

    with st.form(key="personal_form"):
        st.subheader("Personal Budget")
        ps1 = st.number_input("Salary", min_value=0.0, key="p_salary")
        ps2 = st.number_input("Investment Income", min_value=0.0, key="p_invest")
        ps3 = st.number_input("Other Income", min_value=0.0, key="p_other")
        pe1 = st.number_input("Housing", min_value=0.0, key="p_house")
        pe2 = st.number_input("Food", min_value=0.0, key="p_food")
        pe3 = st.number_input("Transport", min_value=0.0, key="p_trans")
        psav1 = st.number_input("Emergency Fund", min_value=0.0, key="p_emerg")
        psav2 = st.number_input("Retirement", min_value=0.0, key="p_retire")
        psav3 = st.number_input("Other Saving", min_value=0.0, key="p_save_other")
        submitted_p = st.form_submit_button("Add Personal Entry")
        if submitted_p:
            add_budget_entry("personal",
                             {"Salary": ps1, "Investments": ps2, "Other": ps3},
                             {"Housing": pe1, "Food": pe2, "Transport": pe3},
                             {"Emergency": psav1, "Retirement": psav2, "Other": psav3})
            st.success("Personal entry added")

    with st.form(key="business_form"):
        st.subheader("Business Budget")
        bs1 = st.number_input("Product Sales", min_value=0.0, key="b_sales")
        bs2 = st.number_input("Service Income", min_value=0.0, key="b_services")
        bs3 = st.number_input("Other Revenue", min_value=0.0, key="b_otherrev")
        be1 = st.number_input("Salaries", min_value=0.0, key="b_salaries")
        be2 = st.number_input("Inventory", min_value=0.0, key="b_inventory")
        be3 = st.number_input("Marketing", min_value=0.0, key="b_marketing")
        bsav1 = st.number_input("R&D", min_value=0.0, key="b_rd")
        bsav2 = st.number_input("Growth Fund", min_value=0.0, key="b_growth")
        bsav3 = st.number_input("Reserves", min_value=0.0, key="b_reserve")
        submitted_b = st.form_submit_button("Add Business Entry")
        if submitted_b:
            add_budget_entry("business",
                             {"Sales": bs1, "Services": bs2, "Other": bs3},
                             {"Salaries": be1, "Inventory": be2, "Marketing": be3},
                             {"R&D": bsav1, "Growth": bsav2, "Reserves": bsav3})
            st.success("Business entry added")

    with st.form(key="government_form"):
        st.subheader("Government / Institutional Budget")
        gs1 = st.number_input("Tax Revenue", min_value=0.0, key="g_tax")
        gs2 = st.number_input("Grants", min_value=0.0, key="g_grant")
        gs3 = st.number_input("Borrowing", min_value=0.0, key="g_borrow")
        ge1 = st.number_input("Education", min_value=0.0, key="g_edu")
        ge2 = st.number_input("Healthcare", min_value=0.0, key="g_health")
        ge3 = st.number_input("Infrastructure", min_value=0.0, key="g_infra")
        gsav1 = st.number_input("Development allocations", min_value=0.0, key="g_dev")
        gsav2 = st.number_input("Defense allocations", min_value=0.0, key="g_def")
        gsav3 = st.number_input("Reserves", min_value=0.0, key="g_res")
        submitted_g = st.form_submit_button("Add Government Entry")
        if submitted_g:
            add_budget_entry("government",
                             {"Tax": gs1, "Grants": gs2, "Borrowing": gs3},
                             {"Education": ge1, "Healthcare": ge2, "Infrastructure": ge3},
                             {"Development": gsav1, "Defense": gsav2, "Reserves": gsav3})
            st.success("Government entry added")

    st.markdown("---")
    st.subheader("Recent Entries (Preview)")
    colp, colb, colg = st.columns(3)
    with colp:
        st.markdown("**Personal**")
        st.dataframe(df_from_entries(st.session_state.personal_entries).sort_values("timestamp", ascending=False).head(6))
    with colb:
        st.markdown("**Business**")
        st.dataframe(df_from_entries(st.session_state.business_entries).sort_values("timestamp", ascending=False).head(6))
    with colg:
        st.markdown("**Government**")
        st.dataframe(df_from_entries(st.session_state.government_entries).sort_values("timestamp", ascending=False).head(6))

# ---------- REPORTS TAB ----------
with tabs[1]:
    st.header("Reports & Attractive Charts")
    # Aggregate numbers
    def sum_field(entries, field):
        return sum(float(e.get(field) or 0) for e in entries)
    agg = pd.DataFrame({
        "Category": ["Personal", "Business", "Government"],
        "Income": [sum_field(st.session_state.personal_entries, "total_income"),
                   sum_field(st.session_state.business_entries, "total_income"),
                   sum_field(st.session_state.government_entries, "total_income")],
        "Expenses": [sum_field(st.session_state.personal_entries, "total_expense"),
                     sum_field(st.session_state.business_entries, "total_expense"),
                     sum_field(st.session_state.government_entries, "total_expense")],
        "Savings": [sum_field(st.session_state.personal_entries, "total_saving"),
                    sum_field(st.session_state.business_entries, "total_saving"),
                    sum_field(st.session_state.government_entries, "total_saving")]
    })

    if agg[["Income", "Expenses", "Savings"]].sum().sum() == 0:
        st.info("No data yet. Add entries on the Budget tab to populate charts.")
    else:
        st.markdown("### Treemap: income / expenses / savings")
        treedata = agg.melt(id_vars="Category", value_vars=["Income","Expenses","Savings"], var_name="Type", value_name="Amount")
        fig_treemap = px.treemap(treedata, path=['Category','Type'], values='Amount',
                                 color='Type', color_discrete_map={"Income":"#60a5fa","Expenses":"#f87171","Savings":"#34d399"},
                                 title="Where the money is")
        fig_treemap.update_layout(margin=dict(t=30,l=0,r=0,b=0))
        st.plotly_chart(fig_treemap, use_container_width=True)

        st.markdown("### Net over time (entries)")
        # Build time-series rows
        rows = []
        for e in st.session_state.personal_entries:
            rows.append({"time": e["timestamp"], "net": e["net"], "category": "Personal"})
        for e in st.session_state.business_entries:
            rows.append({"time": e["timestamp"], "net": e["net"], "category": "Business"})
        for e in st.session_state.government_entries:
            rows.append({"time": e["timestamp"], "net": e["net"], "category": "Government"})
        if rows:
            df_ts = pd.DataFrame(rows)
            df_ts['time'] = pd.to_datetime(df_ts['time'])
            fig_line = px.line(df_ts, x='time', y='net', color='category', markers=True, title="Net over time by category")
            fig_line.update_layout(margin=dict(t=20,l=0,r=0,b=0))
            st.plotly_chart(fig_line, use_container_width=True)

# ---------- NET WORTH TAB ----------
with tabs[2]:
    st.header("Net Worth — Fun & Informative (Free)")
    st.markdown("Enter assets and liabilities. We'll calculate net worth and show playful comparisons.")
    with st.form(key="networth_form"):
        na1 = st.number_input("Cash & bank", min_value=0.0, key="na_cash")
        na2 = st.number_input("Investments", min_value=0.0, key="na_invest")
        na3 = st.number_input("Property value", min_value=0.0, key="na_property")
        na4 = st.number_input("Business equity", min_value=0.0, key="na_business")
        na5 = st.number_input("Other assets", min_value=0.0, key="na_other_assets")
        nl1 = st.number_input("Mortgage", min_value=0.0, key="nl_mortgage")
        nl2 = st.number_input("Loans", min_value=0.0, key="nl_loans")
        nl3 = st.number_input("Credit & other liabilities", min_value=0.0, key="nl_credit")
        submitted_nw = st.form_submit_button("Calculate Net Worth")
        if submitted_nw:
            total_assets = na1 + na2 + na3 + na4 + na5
            total_liabilities = nl1 + nl2 + nl3
            net = total_assets - total_liabilities
            st.session_state.networth = net
            st.success(f"Your net worth is ${net:,.2f}")
            # Benchmarks (changeable)
            richest = 200_000_000_000
            poorest = -1_000_000
            # compute log-relative pos
            def relative_log(v, lo, hi):
                v_log = np.log10(max(v,0) + 1)
                lo_log = np.log10(max(lo,0) + 1)
                hi_log = np.log10(max(hi,1) + 1)
                pos = (v_log - lo_log) / max((hi_log - lo_log), 1e-9)
                return float(np.clip(pos, 0, 1))
            pos = relative_log(abs(net), poorest, richest)
            pct = pos*100
            st.markdown(f"**Relative position on a log scale:** {pct:.2f}% between poorest and richest benchmark.")
            # show gauge-like donut
            fig = go.Figure(data=[go.Pie(labels=["Your Net", "Remaining to Richest"], values=[max(net,0)+1, max(richest - max(net,0), 0)+1], hole=0.6)])
            fig.update_layout(title_text="Net Worth Relative Donut", showlegend=True, margin=dict(t=30,b=10,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

# ---------- GOVERNMENT AUDIT TAB ----------
with tabs[3]:
    st.header("Government Audit Tool — user-provided evidence only")
    st.markdown("Use this to structure audits. This tool stores local entries and can export CSV for sharing.")
    with st.form(key="audit_form"):
        leader = st.text_input("Leader name (e.g., MCA John Doe)", key="audit_leader")
        office = st.selectbox("Office level", ["MCA/Local Rep","MP","Governor","President","Other"], key="audit_office")
        declared_income = st.number_input("Declared income & allowances (annual)", min_value=0.0, key="audit_decl_income")
        declared_assets = st.number_input("Declared personal assets (sum)", min_value=0.0, key="audit_decl_assets")
        contracts_value = st.number_input("Total known contracts value (assoc.)", min_value=0.0, key="audit_contracts")
        claimed_dev = st.number_input("Public project spend claimed", min_value=0.0, key="audit_claimed_spend")
        est_assets = st.number_input("Community-estimated assets", min_value=0.0, key="audit_est_assets")
        notes = st.text_area("Notes / links / evidence", key="audit_notes")
        submitted_audit = st.form_submit_button("Run Audit & Save")
        if submitted_audit:
            declared_capacity = declared_income + declared_assets + 1e-9
            apparent_total = est_assets + contracts_value + claimed_dev
            ratio = apparent_total / declared_capacity if declared_capacity else float("inf")
            result = {
                "leader": leader,
                "office": office,
                "declared_income": declared_income,
                "declared_assets": declared_assets,
                "contracts_value": contracts_value,
                "claimed_dev": claimed_dev,
                "est_assets": est_assets,
                "ratio": ratio,
                "notes": notes,
                "user": st.session_state.user,
                "ts": datetime.utcnow().isoformat()
            }
            st.session_state.audits.append(result)
            st.success("Audit saved locally.")
            # show quick assessment
            st.write(f"Discrepancy ratio (apparent/declared): {ratio:.2f}")
            if ratio > 3:
                st.error("High discrepancy — potential red flag.")
            elif ratio > 1.2:
                st.warning("Moderate discrepancy — follow-up suggested.")
            else:
                st.success("No obvious discrepancy from provided numbers.")
            # pie chart to illustrate spend vs unexplained
            unexplained = max(apparent_total - declared_capacity, 0)
            used = min(apparent_total, declared_capacity)
            fig_p = px.pie(names=["Explained/Used","Unexplained/Excess"], values=[used, unexplained], title=f"{leader} — Explained vs Unexplained (toy view)")
            st.plotly_chart(fig_p, use_container_width=True)

    if st.session_state.audits:
        df_a = pd.DataFrame(st.session_state.audits).sort_values("ts", ascending=False)
        st.markdown("Recent audits (local)")
        st.dataframe(df_a[["ts","leader","office","ratio","user"]].head(8))
        st.download_button("Export audits CSV", df_a.to_csv(index=False), file_name="audits.csv", mime="text/csv")

# ---------- FEEDBACK TAB ----------
with tabs[4]:
    st.header("Feedback & Suggestions")
    fname = st.text_input("Your name (optional)", key="fb_name")
    femail = st.text_input("Your email (optional)", key="fb_email")
    fmsg = st.text_area("Message", key="fb_message")
    if st.button("Send feedback"):
        if not fmsg.strip():
            st.warning("Please write a message before sending.")
        else:
            item = {"name": fname, "email": femail, "message": fmsg, "ts": datetime.utcnow().isoformat()}
            st.session_state.feedback_list.append(item)
            sent = send_admin_email("SmartCalc feedback", json.dumps(item, indent=2))
            if sent:
                st.success("Thanks! Feedback emailed to admin.")
            else:
                st.info("Feedback saved locally (admin email not configured).")

    if st.session_state.feedback_list:
        st.markdown("Recent feedback (local)")
        st.dataframe(pd.DataFrame(st.session_state.feedback_list).sort_values("ts", ascending=False).head(8))

# ---------- SETTINGS TAB ----------
with tabs[5]:
    st.header("Settings & Export")
    st.selectbox("UI currency (display only)", ["USD","KES","EUR","GBP","INR"], index=0, key="ui_currency")
    st.markdown("Export all app data locally (JSON):")
    if st.button("Export all data as JSON"):
        all_data = {
            "personal": st.session_state.personal_entries,
            "business": st.session_state.business_entries,
            "government": st.session_state.government_entries,
            "audits": st.session_state.audits,
            "feedback": st.session_state.feedback_list
        }
        st.download_button("Download JSON", json.dumps(all_data, indent=2), file_name="smartcalc_all.json", mime="application/json")

st.markdown("---")
st.caption("SmartCalc Suite — polished & corrected. Configure EMAIL_USER/EMAIL_PASS/ADMIN_EMAIL in Streamlit secrets or environment variables to enable admin emails.")

