
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import smtplib
from email.mime.text import MIMEText
from streamlit_lottie import st_lottie
import requests

# --------------------------
# Utility: Load Lottie animations
# --------------------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

welcome_animation = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_jcikwtux.json")
audit_animation = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_hvx2gjjb.json")
networth_animation = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_tutvdkg0.json")

# --------------------------
# Page Config
# --------------------------
st.set_page_config(page_title="SmartCalc", page_icon="💡", layout="wide")

# --------------------------
# Custom CSS
# --------------------------
st.markdown("""
    <style>
        /* Dark Neon Theme */
        body {
            background-color: #0d0d0d;
            color: #00e6e6;
        }
        .stTextInput input {
            color: #00ffff !important;
            background: #1a1a1a !important;
            border-radius: 10px !important;
        }
        .stButton>button {
            background: linear-gradient(90deg, #00e6e6, #0066ff);
            color: white !important;
            border-radius: 12px;
            padding: 10px 20px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            background: linear-gradient(90deg, #ff00ff, #00ffff);
        }
        .css-10trblm, .css-1d391kg {
            color: #00e6e6 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------
# Feedback Function
# --------------------------
def save_feedback(name, feedback):
    admin_email = "mumblykilonzo@gmail.com"
    sender = "mumblykilonzo@gmail.com"
    password = "@Frequency24#"

    if admin_email and sender and password:
        try:
            msg = MIMEText(f"Feedback from {name}:\n\n{feedback}")
            msg["Subject"] = "SmartCalc Feedback"
            msg["From"] = sender
            msg["To"] = admin_email

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender, password)
            server.sendmail(sender, [admin_email], msg.as_string())
            server.quit()

            st.success("✅ Feedback sent successfully! Thank you!")
        except Exception as e:
            st.warning(f"⚠️ Could not send feedback via email. Saved locally. Error: {e}")
            with open("feedback.txt", "a") as f:
                f.write(f"{name}: {feedback}\n")
    else:
        with open("feedback.txt", "a") as f:
            f.write(f"{name}: {feedback}\n")
        st.info("💾 Feedback saved locally. (Email not configured)")

# --------------------------
# Welcome Page Before Login
# --------------------------
def welcome_screen():
    st.title("🚀 Welcome to SmartCalc!")
    st_lottie(welcome_animation, height=300, key="welcome")
    st.markdown("""
        ### Your all-in-one **Smart Financial Tool** 💡  
        Track spending, calculate net worth, audit leaders, and visualize insights.  
        🔑 Please sign in to unlock your personal dashboard.
    """)

# --------------------------
# Budget Tracker
# --------------------------
def budget_tracker():
    st.subheader("📊 Budget Tracker")
    categories = ["Housing", "Food", "Transport", "Healthcare", "Entertainment", "Other"]
    amounts = []

    with st.form("budget_form"):
        for c in categories:
            amt = st.number_input(f"{c} Expense:", min_value=0, value=0, step=50)
            amounts.append(amt)
        submitted = st.form_submit_button("Save Budget")

    if submitted:
        df = pd.DataFrame({"Category": categories, "Amount": amounts})
        st.write("### Expense Table")
        st.table(df)

        col1, col2 = st.columns(2)
        with col1:
            st.write("#### 📈 Line Chart")
            st.line_chart(df.set_index("Category"))
        with col2:
            st.write("#### 🥧 Pie Chart")
            fig = px.pie(df, names="Category", values="Amount", title="Expense Distribution")
            st.plotly_chart(fig, use_container_width=True)

# --------------------------
# Net Worth Calculator
# --------------------------
def networth_calculator():
    st.subheader("💰 Net Worth Calculator")
    st_lottie(networth_animation, height=200, key="networth")

    assets = st.number_input("Total Assets (KES)", min_value=0, step=1000)
    liabilities = st.number_input("Total Liabilities (KES)", min_value=0, step=1000)

    if st.button("Calculate Net Worth"):
        networth = assets - liabilities
        st.metric("Your Net Worth", f"KES {networth:,}")

        richest = 270_000_000_000  # Example richest man
        poorest = -500  # Example poorest
        relative = (networth - poorest) / (richest - poorest) * 100
        st.progress(min(max(int(relative), 0), 100))

        if networth < 0:
            st.error("⚠️ You're in the red. Time to cut back on liabilities.")
        elif networth < 1_000_000:
            st.info("💡 Building wealth takes time. Keep saving and investing!")
        else:
            st.success("🚀 You're on your way to financial freedom!")

# --------------------------
# Government Audit Tool
# --------------------------
def government_audit():
    st.subheader("🏛️ Government Leader Audit Tool")
    st_lottie(audit_animation, height=200, key="audit")

    leaders = ["MCA", "MP", "Governor", "Senator", "President"]
    leader = st.selectbox("Select Leader", leaders)

    salary = st.number_input(f"{leader} Salary (KES)", min_value=0, step=10000)
    allowances = st.number_input("Allowances (KES)", min_value=0, step=5000)
    development = st.number_input("Development Spending (KES)", min_value=0, step=10000)

    if st.button("Audit Leader"):
        total_income = salary + allowances
        remaining = total_income - development
        st.metric(f"{leader} Remaining Funds", f"KES {remaining:,}")
        st.warning("👀 Citizens, compare this with real development on the ground!")

# --------------------------
# Feedback Section
# --------------------------
def feedback_section():
    st.subheader("💬 We value your feedback!")
    name = st.text_input("Your Name")
    feedback = st.text_area("Share your thoughts about SmartCalc")
    if st.button("Send Feedback"):
        if name and feedback:
            save_feedback(name, feedback)
        else:
            st.error("⚠️ Please provide both name and feedback.")

# --------------------------
# Navigation
# --------------------------
menu = ["Welcome", "Budget", "Net Worth", "Audit", "Feedback"]
choice = st.sidebar.radio("Navigate", menu)

if choice == "Welcome":
    welcome_screen()
elif choice == "Budget":
    budget_tracker()
elif choice == "Net Worth":
    networth_calculator()
elif choice == "Audit":
    government_audit()
elif choice == "Feedback":
    feedback_section()

         
