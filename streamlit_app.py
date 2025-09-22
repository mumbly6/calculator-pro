import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import random
import os
from streamlit_lottie import st_lottie

# ================================
# 🌟 LOTTIE LOADER
# ================================
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Example animations (replace with your favorites from LottieFiles)
lottie_home = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json")  # money growth
lottie_chart = load_lottieurl("https://assets2.lottiefiles.com/private_files/lf30_editor_z4q6lx8l.json")  # charts
lottie_login = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_5ngs2ksb.json")  # handshake
lottie_audit = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_bhw1ul4g.json")  # magnifying glass
lottie_logout = load_lottieurl("https://assets2.lottiefiles.com/private_files/lf30_editor_hx6bn7vg.json")  # logout tip

# ================================
# 🌟 CUSTOM CSS
# ================================
st.markdown("""
<style>
    body {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #f8f9fa;
        font-family: 'Poppins', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(to right, #11998e, #38ef7d);
        color: white;
        border-radius: 12px;
        font-size: 16px;
        padding: 10px 20px;
        transition: 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.08);
        box-shadow: 0px 0px 25px rgba(56,239,125,0.8);
    }
    .css-1d391kg { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ================================
# 🌟 SESSION STATE
# ================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "income" not in st.session_state:
    st.session_state.income = []
if "networth" not in st.session_state:
    st.session_state.networth = 0

# ================================
# 🌟 LOGIN AREA
# ================================
def login_area():
    st_lottie(lottie_login, height=180, key="login")

    st.subheader("🔑 Login to Elite Finance Hub")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    admin_email = st.secrets.get("ADMIN_EMAIL") if "ADMIN_EMAIL" in st.secrets else os.environ.get("ADMIN_EMAIL")
    admin_pass = st.secrets.get("ADMIN_PASS") if "ADMIN_PASS" in st.secrets else os.environ.get("ADMIN_PASS")

    if st.button("Login"):
        if username == admin_email and password == admin_pass:
            st.session_state.logged_in = True
            st.success(f"🎉 Welcome {username}! Thanks for signing in.")
        else:
            st.error("❌ Invalid credentials. Try again.")

# ================================
# 🌟 LOGOUT AREA WITH FINANCIAL TIPS
# ================================
def logout_area():
    tips = [
        "Invest at least 20% of your income in assets, not liabilities.",
        "Track every shilling: what gets measured gets managed.",
        "Avoid lifestyle inflation: earn more, but keep expenses steady.",
        "Build an emergency fund covering at least 6 months of expenses.",
        "Let compound interest be your best friend: start investing early."
    ]
    st_lottie(lottie_logout, height=180, key="logout")
    st.success(f"💡 Financial Tip: {random.choice(tips)}")
    st.session_state.logged_in = False

# ================================
# 🌟 DASHBOARD TAB
# ================================
def dashboard():
    st_lottie(lottie_home, height=220, key="home")
    st.title("📊 Personal Finance Dashboard")
    st.write("Welcome to your one-stop finance hub. Track, analyze, and compare with style!")

# ================================
# 🌟 EXPENSE TRACKER
# ================================
def expense_tracker():
    st.subheader("💸 Track Your Expenses")
    category = st.selectbox("Category", ["Food", "Transport", "Rent", "Entertainment", "Other"])
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    if st.button("Add Expense"):
        st.session_state.expenses.append({"Category": category, "Amount": amount})
        st.success("Expense added!")

    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        st.write(df)

        fig = px.pie(df, values="Amount", names="Category", hole=0.4, title="Expense Breakdown")
        fig.update_traces(textinfo="percent+label", pull=[0.05]*len(df))
        st_lottie(lottie_chart, height=120, key="chart_expenses")
        st.plotly_chart(fig, use_container_width=True)

# ================================
# 🌟 INCOME MANAGER
# ================================
def income_manager():
    st.subheader("💰 Manage Your Income")
    source = st.text_input("Source")
    amount = st.number_input("Amount", min_value=0.0, step=0.01, key="income_amount")
    if st.button("Add Income"):
        st.session_state.income.append({"Source": source, "Amount": amount})
        st.success("Income added!")

    if st.session_state.income:
        df = pd.DataFrame(st.session_state.income)
        st.write(df)

        fig = px.bar(df, x="Source", y="Amount", title="Income Sources", color="Source", text="Amount")
        fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
        st_lottie(lottie_chart, height=120, key="chart_income")
        st.plotly_chart(fig, use_container_width=True)

# ================================
# 🌟 NET WORTH CALCULATOR
# ================================
def net_worth_calculator():
    st.subheader("📈 Net Worth Calculator")
    assets = st.number_input("Total Assets ($)", min_value=0.0, step=100.0)
    liabilities = st.number_input("Total Liabilities ($)", min_value=0.0, step=100.0)

    if st.button("Calculate Net Worth"):
        networth = assets - liabilities
        st.session_state.networth = networth
        st.success(f"💵 Your Net Worth: ${networth:,.2f}")

        richest = 200_000_000_000  # Elon Musk ballpark
        poorest = -1_000_000
        relative = (networth - poorest) / (richest - poorest) * 100

        gauge = px.scatter(x=[0], y=[networth], title="Net Worth Comparison",
                           labels={"x": "Relative Scale", "y": "Net Worth"})
        st_lottie(lottie_chart, height=120, key="chart_networth")
        st.write(f"🌍 You stand at **{relative:.6f}%** between the poorest and the richest on Earth!")

# ================================
# 🌟 GOVERNMENT AUDIT TOOL
# ================================
def government_audit():
    st.subheader("🏛 Audit Your Leaders")
    st_lottie(lottie_audit, height=180, key="audit")
    leader = st.selectbox("Choose Leader Level", ["MCA", "MP", "Senator", "Governor", "President"])
    salary = st.number_input(f"💵 Official Salary of {leader}", min_value=0.0, step=1000.0)
    allowances = st.number_input(f"🎁 Allowances for {leader}", min_value=0.0, step=1000.0)
    grants = st.number_input(f"📦 Grants/Funds Allocated to {leader}", min_value=0.0, step=1000.0)

    total_received = salary + allowances + grants
    spent = st.number_input(f"🏗 Development Spending Observed for {leader}", min_value=0.0, step=1000.0)

    if st.button("Audit"):
        unexplained = total_received - spent
        data = pd.DataFrame({
            "Category": ["Spent on Development", "Unexplained Balance"],
            "Amount": [spent, unexplained]
        })
        st.write(data)

        fig = px.pie(data, values="Amount", names="Category", title=f"{leader} Audit Report")
        st.plotly_chart(fig, use_container_width=True)

# ================================
# 🌟 MAIN APP
# ================================
def main():
    if not st.session_state.logged_in:
        login_area()
    else:
        st.sidebar.title("🌐 Navigation")
        choice = st.sidebar.radio("Go to", ["Dashboard", "Expenses", "Income", "Net Worth", "Government Audit", "Logout"])

        if choice == "Dashboard":
            dashboard()
        elif choice == "Expenses":
            expense_tracker()
        elif choice == "Income":
            income_manager()
        elif choice == "Net Worth":
            net_worth_calculator()
        elif choice == "Government Audit":
            government_audit()
        elif choice == "Logout":
            logout_area()

if __name__ == "__main__":
    main()
