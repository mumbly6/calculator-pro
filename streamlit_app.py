# streamlit_app.py
# SmartCalc — Full refined Streamlit app (dark-neon theme, Lottie, budgets in row, charts, audit, networth, feedback)
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

# Try to import streamlit-lottie; if missing, app still works with fallbacks
try:
    from streamlit_lottie import st_lottie
    LOTTIE_OK = True
except Exception:
    LOTTIE_OK = False

# -------------------------
# Lottie loader (safe)
# -------------------------
def load_lottieurl(url: str, timeout=6):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

# Lottie assets (change if you prefer)
LOTTIE_WELCOME = "https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json"   # finance growth
LOTTIE_CHART = "https://assets2.lottiefiles.com/private_files/lf30_editor_z4q6lx8l.json"
LOTTIE_LOGIN = "https://assets10.lottiefiles.com/packages/lf20_5ngs2ksb.json"
LOTTIE_AUDIT = "https://assets9.lottiefiles.com/packages/lf20_bhw1ul4g.json"
LOTTIE_LOGOUT = "https://assets2.lottiefiles.com/private_files/lf30_editor_hx6bn7vg.json"

lottie_welcome = load_lottieurl(LOTTIE_WELCOME) if LOTTIE_OK else None
lottie_chart = load_lottieurl(LOTTIE_CHART) if LOTTIE_OK else None
lottie_login = load_lottieurl(LOTTIE_LOGIN) if LOTTIE_OK else None
lottie_audit = load_lottieurl(LOTTIE_AUDIT) if LOTTIE_OK else None
lottie_logout = load_lottieurl(LOTTIE_LOGOUT) if LOTTIE_OK else None

# -------------------------
# Page config + CSS
# -------------------------
st.set_page_config(page_title="SmartCalc", layout="wide", initial_sidebar_state="expanded")

# Inject CSS - dark neon theme, input visibility fixes, animations
st.markdown(
    """
    <style>
    /* Background and base */
    html, body, [class*="css"] {
      background: radial-gradient(circle at 10% 10%, rgba(124,58,237,0.06), transparent 8%),
                  radial-gradient(circle at 90% 90%, rgba(6,182,212,0.04), transparent 8%),
                  linear-gradient(180deg,#071033,#0b1023 80%);
      color: #e6eef8;
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }

    /* Card */
    .card {
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border: 1px solid rgba(124,58,237,0.08);
      border-radius: 12px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(7,12,25,0.6);
      transition: transform .18s ease, box-shadow .18s ease;
      margin-bottom: 12px;
    }
    .card:hover { transform: translateY(-6px); box-shadow: 0 20px 60px rgba(99,102,241,0.12); }

    /* Buttons */
    .neon {
      background: linear-gradient(90deg,#7c3aed,#06b6d4);
      color: white;
      border-radius: 10px;
      padding: 8px 14px;
      font-weight: 700;
      border: none;
      cursor: pointer;
      box-shadow: 0 8px 30px rgba(99,102,241,0.14), 0 0 18px rgba(6,182,212,0.08);
      transition: transform .12s ease;
    }
    .neon:hover { transform: translateY(-3px); box-shadow: 0 30px 80px rgba(99,102,241,0.18); }

    /* Inputs: make typed text visible and fun bluish/cyan */
    input[type="text"], input[type="number"], textarea, .stTextInput>div>input, .stTextArea>div>textarea {
        color: #4ee1ff !important;            /* bright cyan for typed text */
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
    }
    /* Placeholder color */
    ::placeholder {
        color: #80e9ff !important;
        opacity: 0.8 !important;
    }
    /* Focus glow */
    input:focus, textarea:focus, .stTextInput>div>input:focus, .stTextArea>div>textarea:focus {
        outline: none !important;
        border: 2px solid #4ee1ff !important;
        box-shadow: 0 0 12px rgba(78,225,255,0.16) !important;
    }

    /* Muted text */
    .muted { color: rgba(230,238,248,0.7); }

    /* Small animation for tabs */
    .tab-card { animation: fadeIn .45s ease; }
    @keyframes fadeIn { from {opacity:0; transform: translateY(6px);} to {opacity:1; transform:none;} }

    /* Header gradients */
    .title-ghost { background:linear-gradient(90deg,#93c5fd,#7c3aed); -webkit-background-clip:text; color:transparent; font-weight:800; font-size:28px; }

    /* responsive */
    @media (max-width: 720px) {
      .grid-3 { display:block !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Session state init
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
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
if "email_errors" not in st.session_state:
    st.session_state.email_errors = []

# -------------------------
# Email helper (optional)
# -------------------------
def send_admin_email(subject: str, body: str) -> bool:
    try:
        email_user = st.secrets.get("EMAIL_USER") if "EMAIL_USER" in st.secrets else os.environ.get("EMAIL_USER")
        email_pass = st.secrets.get("EMAIL_PASS") if "EMAIL_PASS" in st.secrets else os.environ.get("EMAIL_PASS")
        admin_mail = st.secrets.get("ADMIN_EMAIL") if "ADMIN_EMAIL" in st.secrets else os.environ.get("ADMIN_EMAIL")
        if not (email_user and email_pass and admin_mail):
            return False
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = email_user
        msg["To"] = admin_mail
        msg.set_content(body)
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(email_user, email_pass)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.session_state.email_errors.append(str(e))
        return False

# -------------------------
# Login sidebar (always visible)
# -------------------------
def login_sidebar():
    st.sidebar.header("Account")
    if not st.session_state.logged_in:
        uname = st.sidebar.text_input("Username or Email", key="login_user")
        p = st.sidebar.text_input("Password", type="password", key="login_pass")
        col1, col2 = st.sidebar.columns(2)
        if col1.button("Sign in"):
            if uname.strip() == "":
                st.sidebar.error("Enter username/email")
            else:
                admin_pass = st.secrets.get("ADMIN_PASS") if "ADMIN_PASS" in st.secrets else os.environ.get("ADMIN_PASS")
                if uname.lower() == "admin" and admin_pass and p != admin_pass:
                    st.sidebar.error("Invalid admin password")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user = uname
                    st.sidebar.success(f"Signed in as {uname}")
                    # notify admin (best effort)
                    send_admin_email("SmartCalc login", f"User {uname} signed in at {datetime.utcnow().isoformat()} UTC")
        if col2.button("Continue as guest"):
            st.session_state.logged_in = True
            st.session_state.user = "guest"
            st.sidebar.success("Continuing as guest")
    else:
        st.sidebar.markdown(f"**Signed in as**  \n{st.session_state.user}")
        if st.sidebar.button("Sign out"):
            tip = random.choice([
                "Automate saving 10% of income each month.",
                "Audit your subscriptions — remove one you don't use.",
                "Put extra cash into a low-cost index fund."
            ])
            st.sidebar.success("Signed out. Tip: " + tip)
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()

login_sidebar()

# -------------------------
# Landing content (visible before sign in)
# -------------------------
def landing_view():
    st.markdown("<div class='card tab-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("<div style='padding:6px'>", unsafe_allow_html=True)
        st.markdown("<div class='title-ghost'>SmartCalc</div>", unsafe_allow_html=True)
        st.markdown("<p class='muted'>Welcome — a playful budget tracker with audit tools, beautiful charts, and a neon UI. Sign in (sidebar) or continue as guest to try it out.</p>", unsafe_allow_html=True)
        st.markdown("<ul class='muted'><li>Budget input tables (row-based)</li><li>Charts: Line, Bar, Pie, Treemap</li><li>Net Worth calculator & Audit tool</li><li>Feedback & export</li></ul>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        try:
            if LOTTIE_OK and lottie_welcome:
                st_lottie(lottie_welcome, height=180, key="welcome_l")
            else:
                # fallback image-like metric
                st.markdown("<div style='text-align:center;padding:8px'><div style='font-size:20px;font-weight:700;color:#7c3aed'>Welcome!</div><div class='muted'>Open the sidebar to sign in.</div></div>", unsafe_allow_html=True)
        except Exception:
            st.markdown("<div class='muted'>Welcome — open the sidebar to sign in.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    # quick CTA
    st.markdown("<div class='card'><div style='display:flex;justify-content:space-between;align-items:center'><div><strong>Try the demo:</strong> click 'Continue as guest' in the sidebar to explore the app.</div><div><button class='neon' onclick=\"window.scrollTo(0, document.body.scrollHeight);\">Explore</button></div></div></div>", unsafe_allow_html=True)

# Show landing and stop if not logged in
if not st.session_state.logged_in:
    landing_view()
    st.stop()

# -------------------------
# Helpers for budget entries
# -------------------------
def add_budget_entry(kind: str, income_map: dict, expense_map: dict, saving_map: dict):
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
    if kind == "personal":
        st.session_state.personal_entries.append(entry)
    elif kind == "business":
        st.session_state.business_entries.append(entry)
    elif kind == "government":
        st.session_state.government_entries.append(entry)

def df_preview(entries):
    if not entries:
        return pd.DataFrame(columns=["timestamp","total_income","total_expense","total_saving","net","user"])
    df = pd.DataFrame(entries)
    return df[["timestamp","total_income","total_expense","total_saving","net","user"]]

# -------------------------
# Header (after sign-in)
# -------------------------
colL, colR = st.columns([3,1])
with colL:
    st.markdown("<h1 style='margin:0;'><span class='title-ghost'>SmartCalc</span></h1>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Neon-styled budget & audit studio — track budgets, visualize, and audit.</div>", unsafe_allow_html=True)
with colR:
    total_net = sum(e["net"] for e in (st.session_state.personal_entries + st.session_state.business_entries + st.session_state.government_entries))
    st.markdown(f"<div style='font-weight:800;color:#7c3aed;'>Total Net: ${total_net:,.2f}</div>", unsafe_allow_html=True)

if LOTTIE_OK and lottie_chart:
    try:
        st_lottie(lottie_chart, height=120, key="l_top_chart")
    except Exception:
        pass

st.markdown("---")

# -------------------------
# Main Tabs
# -------------------------
tabs = st.tabs(["Budget", "Reports", "Net Worth", "Gov Audit", "Feedback", "Settings"])

# ---------- BUDGET ----------
with tabs[0]:
    st.markdown("<div class='card tab-card'>", unsafe_allow_html=True)
    st.subheader("Budgets (Personal | Business | Government)")
    # three column row layout
    c1, c2, c3 = st.columns(3, gap="large")
    # Personal
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("### Personal")
        p_salary = st.number_input("Salary", min_value=0.0, format="%.2f", key="p_salary")
        p_invest = st.number_input("Investments", min_value=0.0, format="%.2f", key="p_invest")
        p_other = st.number_input("Other income", min_value=0.0, format="%.2f", key="p_other")
        p_house = st.number_input("Housing", min_value=0.0, format="%.2f", key="p_house")
        p_food = st.number_input("Food", min_value=0.0, format="%.2f", key="p_food")
        p_trans = st.number_input("Transport", min_value=0.0, format="%.2f", key="p_trans")
        p_save = st.number_input("Savings", min_value=0.0, format="%.2f", key="p_save")
        if st.button("Add Personal Entry", key="add_personal"):
            add_budget_entry("personal",
                             {"Salary": p_salary, "Investments": p_invest, "Other": p_other},
                             {"Housing": p_house, "Food": p_food, "Transport": p_trans},
                             {"Savings": p_save})
            st.success("Personal entry saved")
        st.markdown("</div>", unsafe_allow_html=True)
    # Business
    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("### Business")
        b_sales = st.number_input("Product sales", min_value=0.0, format="%.2f", key="b_sales")
        b_service = st.number_input("Service income", min_value=0.0, format="%.2f", key="b_service")
        b_other = st.number_input("Other revenue", min_value=0.0, format="%.2f", key="b_other")
        b_sal = st.number_input("Salaries", min_value=0.0, format="%.2f", key="b_sal")
        b_inv = st.number_input("Inventory", min_value=0.0, format="%.2f", key="b_inv")
        b_mark = st.number_input("Marketing", min_value=0.0, format="%.2f", key="b_mark")
        b_res = st.number_input("Reserves", min_value=0.0, format="%.2f", key="b_res")
        if st.button("Add Business Entry", key="add_business"):
            add_budget_entry("business",
                             {"Sales": b_sales, "Service": b_service, "Other": b_other},
                             {"Salaries": b_sal, "Inventory": b_inv, "Marketing": b_mark},
                             {"Reserves": b_res})
            st.success("Business entry saved")
        st.markdown("</div>", unsafe_allow_html=True)
    # Government
    with c3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("### Government / Institutional")
        g_tax = st.number_input("Tax revenue", min_value=0.0, format="%.2f", key="g_tax")
        g_grant = st.number_input("Grants", min_value=0.0, format="%.2f", key="g_grant")
        g_borrow = st.number_input("Borrowing", min_value=0.0, format="%.2f", key="g_borrow")
        g_edu = st.number_input("Education spend", min_value=0.0, format="%.2f", key="g_edu")
        g_health = st.number_input("Healthcare spend", min_value=0.0, format="%.2f", key="g_health")
        g_infra = st.number_input("Infrastructure spend", min_value=0.0, format="%.2f", key="g_infra")
        g_dev = st.number_input("Development allocations", min_value=0.0, format="%.2f", key="g_dev")
        if st.button("Add Government Entry", key="add_government"):
            add_budget_entry("government",
                             {"Tax": g_tax, "Grants": g_grant, "Borrowing": g_borrow},
                             {"Education": g_edu, "Healthcare": g_health, "Infrastructure": g_infra},
                             {"Development": g_dev})
            st.success("Government entry saved")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Recent entries preview")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.write("Personal")
        st.dataframe(df_preview(st.session_state.personal_entries).sort_values("timestamp", ascending=False).head(6))
    with r2:
        st.write("Business")
        st.dataframe(df_preview(st.session_state.business_entries).sort_values("timestamp", ascending=False).head(6))
    with r3:
        st.write("Government")
        st.dataframe(df_preview(st.session_state.government_entries).sort_values("timestamp", ascending=False).head(6))

# ---------- REPORTS ----------
with tabs[1]:
    st.header("Reports — Line, Pie, Bar, Treemap")
    def sum_key(entries, key):
        total = 0.0
        for e in entries:
            try:
                total += float(e.get(key, 0))
            except Exception:
                total += 0.0
        return total

    agg = pd.DataFrame({
        "Category": ["Personal", "Business", "Government"],
        "Income": [sum_key(st.session_state.personal_entries, "total_income"),
                   sum_key(st.session_state.business_entries, "total_income"),
                   sum_key(st.session_state.government_entries, "total_income")],
        "Expenses": [sum_key(st.session_state.personal_entries, "total_expense"),
                     sum_key(st.session_state.business_entries, "total_expense"),
                     sum_key(st.session_state.government_entries, "total_expense")],
        "Savings": [sum_key(st.session_state.personal_entries, "total_saving"),
                    sum_key(st.session_state.business_entries, "total_saving"),
                    sum_key(st.session_state.government_entries, "total_saving")]
    })

    if agg[["Income","Expenses","Savings"]].sum().sum() == 0:
        st.info("No data yet — add entries on the Budget tab to populate charts.")
    else:
        # Treemap
        treedata = agg.melt(id_vars="Category", value_vars=["Income","Expenses","Savings"], var_name="Type", value_name="Amount")
        fig_tm = px.treemap(treedata, path=['Category','Type'], values='Amount',
                            color='Type', color_discrete_map={"Income":"#06b6d4","Expenses":"#fb7185","Savings":"#34d399"},
                            title="Distribution: Income / Expenses / Savings")
        fig_tm.update_layout(margin=dict(t=40,l=0,r=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_tm, use_container_width=True)

        st.markdown("### Expense breakdown (Pie & Bar)")
        cp, cb = st.columns(2)
        with cp:
            expense_totals = agg[["Category","Expenses"]]
            fig_p = px.pie(expense_totals, names="Category", values="Expenses", hole=0.45, title="Expenses by Category")
            fig_p.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_p, use_container_width=True)
        with cb:
            fig_b = go.Figure()
            fig_b.add_trace(go.Bar(x=agg["Category"], y=agg["Income"], name="Income", marker_color="#06b6d4"))
            fig_b.add_trace(go.Bar(x=agg["Category"], y=agg["Expenses"], name="Expenses", marker_color="#fb7185"))
            fig_b.update_layout(barmode='group', title="Income vs Expenses by Category", margin=dict(t=40))
            st.plotly_chart(fig_b, use_container_width=True)

        # time series net
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
            fig_line = px.line(df_ts, x='time', y='net', color='cat', markers=True, title="Net over time")
            fig_line.update_layout(margin=dict(t=30,l=0,r=0,b=0))
            st.plotly_chart(fig_line, use_container_width=True)

# ---------- NET WORTH ----------
with tabs[2]:
    st.header("Net Worth — playful and informative")
    with st.form("networth_form"):
        na_cash = st.number_input("Cash & bank", min_value=0.0, format="%.2f", key="na_cash")
        na_inv = st.number_input("Investments", min_value=0.0, format="%.2f", key="na_inv")
        na_prop = st.number_input("Property", min_value=0.0, format="%.2f", key="na_prop")
        nl_mort = st.number_input("Mortgage", min_value=0.0, format="%.2f", key="nl_mort")
        nl_loans = st.number_input("Loans", min_value=0.0, format="%.2f", key="nl_loans")
        submitted = st.form_submit_button("Calculate Net Worth")
        if submitted:
            total_assets = na_cash + na_inv + na_prop
            total_liabs = nl_mort + nl_loans
            net = total_assets - total_liabs
            st.session_state.networth = net
            st.success(f"Your net worth: ${net:,.2f}")
            richest = 200_000_000_000
            poorest = -1_000_000
            def rel_log(v, lo, hi):
                vlog = np.log10(max(v,0)+1)
                lolog = np.log10(max(lo,0)+1)
                hilog = np.log10(max(hi,1)+1)
                pos = (vlog - lolog) / max((hilog-lolog), 1e-9)
                return float(np.clip(pos,0,1))
            pos = rel_log(abs(net), poorest, richest)
            st.markdown(f"**Relative position (log scale):** {pos*100:.2f}%")
            fig = go.Figure(data=[go.Pie(labels=["You","Gap to richest"], values=[max(net,0)+1, max(richest-max(net,0),0)+1], hole=0.6)])
            fig.update_layout(title_text="Net Worth Relative (toy view)", margin=dict(t=30))
            st.plotly_chart(fig, use_container_width=True)

# ---------- GOVERNMENT AUDIT ----------
with tabs[3]:
    st.header("Government Audit Tool — structure evidence")
    with st.form("audit_form"):
        leader = st.text_input("Leader name", key="audit_leader")
        office = st.selectbox("Office level", ["MCA/Local Rep","MP","Senator","Governor","President"], key="audit_office")
        declared_income = st.number_input("Declared income & allowances", min_value=0.0, format="%.2f", key="declared_income")
        declared_assets = st.number_input("Declared assets", min_value=0.0, format="%.2f", key="declared_assets")
        known_contracts = st.number_input("Known contracts total", min_value=0.0, format="%.2f", key="known_contracts")
        claimed_spend = st.number_input("Claimed project spend", min_value=0.0, format="%.2f", key="claimed_spend")
        est_assets = st.number_input("Community-estimated assets", min_value=0.0, format="%.2f", key="est_assets")
        notes = st.text_area("Notes / Evidence", key="audit_notes")
        submit_audit = st.form_submit_button("Run Audit")
        if submit_audit:
            declared_capacity = declared_income + declared_assets + 1e-9
            apparent_total = est_assets + known_contracts + claimed_spend
            ratio = apparent_total / declared_capacity if declared_capacity else float("inf")
            audit_entry = {
                "leader": leader, "office": office, "declared_income": declared_income,
                "declared_assets": declared_assets, "known_contracts": known_contracts,
                "claimed_spend": claimed_spend, "est_assets": est_assets, "notes": notes,
                "ratio": ratio, "user": st.session_state.user, "timestamp": datetime.utcnow().isoformat()
            }
            st.session_state.audits.append(audit_entry)
            st.write(f"Discrepancy ratio (apparent/declared): {ratio:.2f}")
            if ratio > 3:
                st.error("High discrepancy — potential red flag.")
            elif ratio > 1.2:
                st.warning("Moderate discrepancy — follow-up suggested.")
            else:
                st.success("No obvious discrepancy from provided numbers.")
            used = min(apparent_total, declared_capacity)
            unexplained = max(apparent_total - declared_capacity, 0)
            fig_a = px.pie(names=["Explained/Used","Unexplained/Excess"], values=[used, unexplained], title=f"{leader} — Explained vs Unexplained")
            st.plotly_chart(fig_a, use_container_width=True)

    if st.session_state.audits:
        st.markdown("Recent audits (local)")
        st.dataframe(pd.DataFrame(st.session_state.audits).sort_values("timestamp", ascending=False).head(8))
        st.download_button("Export audits CSV", pd.DataFrame(st.session_state.audits).to_csv(index=False), file_name="audits.csv", mime="text/csv")

# ---------- FEEDBACK ----------
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
            st.session_state.feedback.append(item)
            sent = send_admin_email("SmartCalc feedback", json.dumps(item, indent=2))
            if sent:
                st.success("Thanks! Feedback emailed to admin.")
            else:
                # friendlier local-save message
                st.success("Feedback saved locally — thank you!")

    if st.session_state.feedback:
        st.markdown("Recent feedback (local)")
        st.dataframe(pd.DataFrame(st.session_state.feedback).sort_values("ts", ascending=False).head(8))

# ---------- SETTINGS ----------
with tabs[5]:
    st.header("Settings & Export")
    st.selectbox("UI currency (display only)", ["USD","KES","EUR","GBP","INR"], index=0, key="ui_currency")
    if st.button("Export all data (JSON)"):
        payload = {
            "personal": st.session_state.personal_entries,
            "business": st.session_state.business_entries,
            "government": st.session_state.government_entries,
            "audits": st.session_state.audits,
            "feedback": st.session_state.feedback
        }
        st.download_button("Download JSON", json.dumps(payload, indent=2), file_name="smartcalc_data.json", mime="application/json")

st.markdown("---")
st.caption("SmartCalc — configure EMAIL_USER/EMAIL_PASS/ADMIN_EMAIL in Streamlit secrets or environment variables to enable admin emails.")


         
