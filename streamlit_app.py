# streamlit_app.py
# Dark-neon, animated SmartCalc Suite (polished)
# Run: py -m streamlit run streamlit_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import os
import random
import smtplib
from email.message import EmailMessage
from datetime import datetime

# Try to import streamlit-lottie; if missing, app still works (fallback)
try:
    from streamlit_lottie import st_lottie
    LOTTIE_OK = True
except Exception:
    LOTTIE_OK = False

# ---------- LOTTIE LOADER ----------
def load_lottieurl(url: str, timeout=6):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

# Example Lottie assets (change if you prefer)
LOTTIE_HOME = "https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json"
LOTTIE_CHART = "https://assets2.lottiefiles.com/private_files/lf30_editor_z4q6lx8l.json"
LOTTIE_LOGIN = "https://assets10.lottiefiles.com/packages/lf20_5ngs2ksb.json"
LOTTIE_AUDIT = "https://assets9.lottiefiles.com/packages/lf20_bhw1ul4g.json"
LOTTIE_LOGOUT = "https://assets2.lottiefiles.com/private_files/lf30_editor_hx6bn7vg.json"

lottie_home = load_lottieurl(LOTTIE_HOME) if LOTTIE_OK else None
lottie_chart = load_lottieurl(LOTTIE_CHART) if LOTTIE_OK else None
lottie_login = load_lottieurl(LOTTIE_LOGIN) if LOTTIE_OK else None
lottie_audit = load_lottieurl(LOTTIE_AUDIT) if LOTTIE_OK else None
lottie_logout = load_lottieurl(LOTTIE_LOGOUT) if LOTTIE_OK else None

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="SmartCalc — Neon", layout="wide", initial_sidebar_state="expanded")

# ---------- CSS: Dark neon theme + animations ----------
st.markdown(
    """
    <style>
    /* Background */
    html, body, [class*="css"]  {
      background: radial-gradient(1200px 600px at 10% 10%, rgba(124,58,237,0.12), transparent 10%),
                  radial-gradient(900px 400px at 90% 90%, rgba(14,165,233,0.08), transparent 10%),
                  linear-gradient(180deg,#030615,#071029 70%);
      color: #e6eef8;
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }

    /* Cards */
    .card {
      background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015));
      border: 1px solid rgba(124,58,237,0.15);
      border-radius: 12px;
      padding: 18px;
      box-shadow: 0 6px 30px rgba(0,0,0,0.6);
      transition: transform .18s ease, box-shadow .18s ease;
    }
    .card:hover { transform: translateY(-6px); box-shadow: 0 18px 60px rgba(124,58,237,0.16); }

    /* Neon buttons */
    .neon-btn {
      background: linear-gradient(90deg,#7c3aed,#06b6d4);
      color: white;
      border: none;
      padding: 10px 14px;
      border-radius: 10px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 6px 24px rgba(99,102,241,0.12), 0 0 12px rgba(6,182,212,0.12);
      transition: transform .12s ease;
    }
    .neon-btn:hover { transform: translateY(-3px); box-shadow: 0 22px 60px rgba(99,102,241,0.2), 0 0 28px rgba(6,182,212,0.18); }

    /* Metrics */
    .neon-metric { font-size:22px; color: #7c3aed; font-weight:800; }
    .muted { color: rgba(230,238,248,0.65); }

    /* Small animations for list entries */
    .entry { padding: 8px; border-radius: 8px; transition: transform .12s ease, background .12s ease; }
    .entry:hover { transform: translateX(6px); background: rgba(124,58,237,0.03); }

    /* Fancy headers */
    .neon-h1 {
      font-size:34px; font-weight:800;
      background: linear-gradient(90deg,#93c5fd,#7c3aed);
      -webkit-background-clip: text; color: transparent;
    }

    /* Responsive tweaks */
    @media (max-width:640px) {
      .neon-h1 { font-size:24px; }
      .neon-metric { font-size:18px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- SESSION STATE ----------
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
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "networth" not in st.session_state:
    st.session_state.networth = None

# ---------- EMAIL HELPER (safe) ----------
def send_admin_email(subject: str, body: str) -> bool:
    """Send an email if secrets configured. Fails silently (returns False) if not configured."""
    try:
        # Prefer Streamlit secrets
        email_user = st.secrets["EMAIL_USER"] if "EMAIL_USER" in st.secrets else os.environ.get("EMAIL_USER")
        email_pass = st.secrets["EMAIL_PASS"] if "EMAIL_PASS" in st.secrets else os.environ.get("EMAIL_PASS")
        admin_email = st.secrets["ADMIN_EMAIL"] if "ADMIN_EMAIL" in st.secrets else os.environ.get("ADMIN_EMAIL")
        if not (email_user and email_pass and admin_email):
            return False
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = email_user
        msg["To"] = admin_email
        msg.set_content(body)
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.starttls()
            s.login(email_user, email_pass)
            s.send_message(msg)
        return True
    except Exception as e:
        # Log errors in session but don't crash
        errs = st.session_state.get("email_errors", [])
        errs.append(str(e))
        st.session_state["email_errors"] = errs
        return False

# ---------- LOGIN (sidebar) ----------
def login_sidebar():
    st.sidebar.markdown("## Account")
    if not st.session_state.auth:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Sign in"):
            if username.strip() == "":
                st.sidebar.error("Enter a username")
            else:
                admin_pass = st.secrets.get("ADMIN_PASS") if "ADMIN_PASS" in st.secrets else os.environ.get("ADMIN_PASS")
                if username.lower() == "admin" and admin_pass and password != admin_pass:
                    st.sidebar.error("Invalid admin password")
                else:
                    st.session_state.auth = True
                    st.session_state.user = username
                    st.sidebar.success(f"Signed in as {username}")
                    send_admin_email("SmartCalc: login", f"User {username} signed in at {datetime.utcnow().isoformat()}")
        if st.sidebar.button("Continue as guest"):
            st.session_state.auth = True
            st.session_state.user = "guest"
            st.sidebar.success("Continuing as guest")
    else:
        st.sidebar.markdown(f"**Signed in as**  \n{st.session_state.user}")
        if st.sidebar.button("Sign out"):
            tip = random.choice([
                "Automate 10% savings each month.",
                "Reduce one recurring subscription this month.",
                "Put extra cash into high-yield savings."
            ])
            st.sidebar.success("Signed out. Tip: " + tip)
            st.session_state.auth = False
            st.session_state.user = None
            st.experimental_rerun()

login_sidebar()
if not st.session_state.auth:
    st.stop()

# ---------- SMALL HELPERS ----------
def add_entry(kind, income_map, expense_map, saving_map):
    total_income = sum(float(v or 0) for v in income_map.values())
    total_expenses = sum(float(v or 0) for v in expense_map.values())
    total_saving = sum(float(v or 0) for v in saving_map.values())
    net = total_income - total_expenses - total_saving
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "income": income_map,
        "expense": expense_map,
        "saving": saving_map,
        "total_income": total_income,
        "total_expense": total_expenses,
        "total_saving": total_saving,
        "net": net,
        "user": st.session_state.user
    }
    if kind == "personal":
        st.session_state.personal_entries.append(entry)
    elif kind == "business":
        st.session_state.business_entries.append(entry)
    else:
        st.session_state.government_entries.append(entry)

def df_preview(entries):
    if not entries:
        return pd.DataFrame(columns=["timestamp","total_income","total_expense","total_saving","net","user"])
    df = pd.DataFrame(entries)
    return df[["timestamp","total_income","total_expense","total_saving","net","user"]]

# ---------- HERO ----------
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("<div class='neon-h1'>SmartCalc — Neon Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Dark, animated, startup-grade personal & civic finance tools.</div>", unsafe_allow_html=True)
with col2:
    total_net = sum(e["net"] for e in (st.session_state.personal_entries + st.session_state.business_entries + st.session_state.government_entries))
    st.markdown(f"<div class='neon-metric'>Total Net (all): <strong>${total_net:,.2f}</strong></div>", unsafe_allow_html=True)

st.markdown("---")

# ---------- TABS ----------
tabs = st.tabs(["Budget", "Reports", "Net Worth", "Gov Audit", "Feedback", "Settings"])

# ---- Budget tab ----
with tabs[0]:
    st.header("Budget — Add Entries")
    pcol, bcol, gcol = st.columns(3)

    with st.form("personal_form"):
        st.subheader("Personal")
        p_salary = st.number_input("Salary", min_value=0.0, key="p_salary")
        p_inv = st.number_input("Investment income", min_value=0.0, key="p_inv")
        p_other = st.number_input("Other income", min_value=0.0, key="p_other")
        e_house = st.number_input("Housing", min_value=0.0, key="e_house")
        e_food = st.number_input("Food", min_value=0.0, key="e_food")
        e_trans = st.number_input("Transport", min_value=0.0, key="e_trans")
        s_emerg = st.number_input("Emergency savings", min_value=0.0, key="s_emerg")
        s_ret = st.number_input("Retirement", min_value=0.0, key="s_ret")
        submitted_p = st.form_submit_button("Add Personal Entry", help="Saves your personal entry locally")
        if submitted_p:
            add_entry("personal",
                      {"Salary": p_salary, "Invest": p_inv, "Other": p_other},
                      {"Housing": e_house, "Food": e_food, "Transport": e_trans},
                      {"Emergency": s_emerg, "Retirement": s_ret, "Other": 0})
            st.success("Added personal entry")

    with st.form("business_form"):
        st.subheader("Business")
        b_sales = st.number_input("Sales", min_value=0.0, key="b_sales")
        b_serv = st.number_input("Service income", min_value=0.0, key="b_serv")
        b_other = st.number_input("Other revenue", min_value=0.0, key="b_other")
        be_sal = st.number_input("Salaries", min_value=0.0, key="be_sal")
        be_inv = st.number_input("Inventory", min_value=0.0, key="be_inv")
        be_mkt = st.number_input("Marketing", min_value=0.0, key="be_mkt")
        bs_rd = st.number_input("R&D", min_value=0.0, key="bs_rd")
        submitted_b = st.form_submit_button("Add Business Entry")
        if submitted_b:
            add_entry("business",
                      {"Sales": b_sales, "Service": b_serv, "Other": b_other},
                      {"Salaries": be_sal, "Inventory": be_inv, "Marketing": be_mkt},
                      {"R&D": bs_rd, "Other": 0, "Reserves": 0})
            st.success("Added business entry")

    with st.form("gov_form"):
        st.subheader("Government")
        g_tax = st.number_input("Tax revenue", min_value=0.0, key="g_tax")
        g_grant = st.number_input("Grants", min_value=0.0, key="g_grant")
        g_borrow = st.number_input("Borrowing", min_value=0.0, key="g_borrow")
        ge_edu = st.number_input("Education", min_value=0.0, key="ge_edu")
        ge_health = st.number_input("Healthcare", min_value=0.0, key="ge_health")
        ge_infra = st.number_input("Infrastructure", min_value=0.0, key="ge_infra")
        gs_dev = st.number_input("Development allocations", min_value=0.0, key="gs_dev")
        submitted_g = st.form_submit_button("Add Government Entry")
        if submitted_g:
            add_entry("government",
                      {"Tax": g_tax, "Grants": g_grant, "Borrowing": g_borrow},
                      {"Education": ge_edu, "Healthcare": ge_health, "Infrastructure": ge_infra},
                      {"Development": gs_dev, "Defense": 0, "Reserves": 0})
            st.success("Added government entry")

    st.markdown("---")
    st.subheader("Recent entries preview")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Personal**")
        st.dataframe(df_preview(st.session_state.personal_entries).sort_values("timestamp", ascending=False).head(6))
    with c2:
        st.markdown("**Business**")
        st.dataframe(df_preview(st.session_state.business_entries).sort_values("timestamp", ascending=False).head(6))
    with c3:
        st.markdown("**Government**")
        st.dataframe(df_preview(st.session_state.government_entries).sort_values("timestamp", ascending=False).head(6))

# ---- Reports tab ----
with tabs[1]:
    st.header("Reports — Attractive Charts")
    def aggsum(entries, key):
        return sum(float(e.get(key) or 0) for e in entries)

    agg = pd.DataFrame({
        "Category": ["Personal","Business","Government"],
        "Income": [aggsum(st.session_state.personal_entries, "total_income"),
                   aggsum(st.session_state.business_entries, "total_income"),
                   aggsum(st.session_state.government_entries, "total_income")],
        "Expenses": [aggsum(st.session_state.personal_entries, "total_expense"),
                     aggsum(st.session_state.business_entries, "total_expense"),
                     aggsum(st.session_state.government_entries, "total_expense")],
        "Savings": [aggsum(st.session_state.personal_entries, "total_saving"),
                    aggsum(st.session_state.business_entries, "total_saving"),
                    aggsum(st.session_state.government_entries, "total_saving")]
    })

    if agg[["Income","Expenses","Savings"]].sum().sum() == 0:
        st.info("No data yet. Add entries in Budget to populate charts.")
    else:
        st.markdown("### Treemap — Income/Expense/Savings")
        treedata = agg.melt(id_vars="Category", value_vars=["Income","Expenses","Savings"], var_name="Type", value_name="Amount")
        fig_tm = px.treemap(treedata, path=['Category','Type'], values='Amount',
                            color='Type', color_discrete_map={"Income":"#06b6d4","Expenses":"#fb7185","Savings":"#34d399"})
        fig_tm.update_layout(margin=dict(t=30,l=0,r=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_tm, use_container_width=True)

        st.markdown("### Net over time")
        rows = []
        for e in st.session_state.personal_entries:
            rows.append({"time": e["timestamp"], "net": e["net"], "cat": "Personal"})
        for e in st.session_state.business_entries:
            rows.append({"time": e["timestamp"], "net": e["net"], "cat": "Business"})
        for e in st.session_state.government_entries:
            rows.append({"time": e["timestamp"], "net": e["net"], "cat": "Government"})
        if rows:
            df_ts = pd.DataFrame(rows)
            df_ts['time'] = pd.to_datetime(df_ts['time'])
            fig_line = px.line(df_ts, x='time', y='net', color='cat', markers=True, title="Net over time by category")
            fig_line.update_layout(margin=dict(t=20,l=0,r=0,b=0))
            st.plotly_chart(fig_line, use_container_width=True)

# ---- Net Worth tab ----
with tabs[2]:
    st.header("Net Worth — playful comparison")
    with st.form("nw"):
        a_cash = st.number_input("Cash & bank", min_value=0.0, key="a_cash")
        a_inv = st.number_input("Investments", min_value=0.0, key="a_inv")
        a_prop = st.number_input("Property", min_value=0.0, key="a_prop")
        l_mort = st.number_input("Mortgage", min_value=0.0, key="l_mort")
        l_loan = st.number_input("Loans", min_value=0.0, key="l_loan")
        submit_nw = st.form_submit_button("Compute Net Worth")
        if submit_nw:
            assets = a_cash + a_inv + a_prop
            liabs = l_mort + l_loan
            net = assets - liabs
            st.session_state.networth = net
            st.success(f"Net worth: ${net:,.2f}")
            # playful relative
            richest = 200_000_000_000  # changeable
            poorest = -1_000_000
            def rel_log(v, lo, hi):
                vlog = np.log10(max(v,0)+1)
                lolog = np.log10(max(lo,0)+1)
                hilog = np.log10(max(hi,1)+1)
                pos = (vlog - lolog) / max((hilog-lolog), 1e-9)
                return float(np.clip(pos,0,1))
            pos = rel_log(abs(net), poorest, richest)
            st.markdown(f"**Relative position (log scale):** {pos*100:.2f}%")
            # donut visualization
            figp = go.Figure(data=[go.Pie(labels=["You","Gap to richest"], values=[max(net,0)+1, max(richest-max(net,0),0)+1], hole=0.6)])
            figp.update_layout(title_text="Net Worth Relative (toy view)", margin=dict(t=30,b=0))
            st.plotly_chart(figp, use_container_width=True)

# ---- Gov Audit tab ----
with tabs[3]:
    st.header("Government Audit — structure evidence")
    with st.form("audit"):
        leader = st.text_input("Leader name", key="audit_leader")
        office = st.selectbox("Office", ["MCA","MP","Governor","President","Other"], key="audit_office")
        dec_income = st.number_input("Declared income", min_value=0.0, key="dec_income")
        dec_assets = st.number_input("Declared assets", min_value=0.0, key="dec_assets")
        known_contracts = st.number_input("Known contracts total", min_value=0.0, key="known_contracts")
        claimed_spend = st.number_input("Claimed development spending", min_value=0.0, key="claimed_spend")
        est_assets = st.number_input("Community-estimated assets", min_value=0.0, key="est_assets")
        notes = st.text_area("Notes / links (evidence)", key="audit_notes")
        sub_a = st.form_submit_button("Run audit")
        if sub_a:
            declared_capacity = dec_income + dec_assets + 1e-9
            apparent = est_assets + known_contracts + claimed_spend
            ratio = apparent / declared_capacity if declared_capacity else float("inf")
            audit = {"leader": leader, "office": office, "declared_capacity": declared_capacity, "apparent": apparent, "ratio": ratio, "notes": notes, "user": st.session_state.user, "ts": datetime.utcnow().isoformat()}
            st.session_state.audits.append(audit)
            st.write(f"Discrepancy ratio: {ratio:.2f}")
            if ratio > 3:
                st.error("High discrepancy — red flag")
            elif ratio > 1.2:
                st.warning("Moderate discrepancy — follow up")
            else:
                st.success("No obvious discrepancy from provided numbers")
            # pie
            used = min(apparent, declared_capacity)
            unexplained = max(apparent - declared_capacity, 0)
            fig_a = px.pie(names=["Explained","Unexplained"], values=[used, unexplained], title=f"{leader} — Explained vs Unexplained")
            st.plotly_chart(fig_a, use_container_width=True)
    if st.session_state.audits:
        st.markdown("Recent audits (local)")
        df_a = pd.DataFrame(st.session_state.audits).sort_values("ts", ascending=False)
        st.dataframe(df_a[["ts","leader","office","ratio","user"]].head(8))
        st.download_button("Export audits CSV", df_a.to_csv(index=False), file_name="audits.csv", mime="text/csv")

# ---- Feedback tab ----
with tabs[4]:
    st.header("Feedback")
    fname = st.text_input("Your name (optional)", key="fb_name")
    femail = st.text_input("Your email (optional)", key="fb_email")
    fmsg = st.text_area("Message", key="fb_msg")
    if st.button("Send feedback"):
        if not fmsg.strip():
            st.warning("Please write a message.")
        else:
            item = {"name": fname, "email": femail, "message": fmsg, "ts": datetime.utcnow().isoformat()}
            st.session_state.feedback.append(item)
            sent = send_admin_email("SmartCalc feedback", json.dumps(item, indent=2))
            if sent:
                st.success("Feedback emailed to admin.")
            else:
                st.success("Thanks! Feedback saved locally.")

    if st.session_state.feedback:
        st.markdown("Recent feedback (local)")
        st.dataframe(pd.DataFrame(st.session_state.feedback).sort_values("ts", ascending=False).head(8))

# ---- Settings tab ----
with tabs[5]:
    st.header("Settings & Export")
    st.selectbox("UI currency (display only)", ["USD","KES","EUR","GBP","INR"], index=0, key="ui_cur")
    if st.button("Export all data (JSON)"):
        payload = {
            "personal": st.session_state.personal_entries,
            "business": st.session_state.business_entries,
            "government": st.session_state.government_entries,
            "audits": st.session_state.audits,
            "feedback": st.session_state.feedback
        }
        st.download_button("Download JSON", json.dumps(payload, indent=2), file_name="smartcalc_all.json", mime="application/json")

st.markdown("---")
st.caption("Dark-Neon SmartCalc — configure EMAIL_USER/EMAIL_PASS/ADMIN_EMAIL in secrets to enable email notifications.")


