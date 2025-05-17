import streamlit as st
from openai import OpenAI
import io
import re
import requests
from datetime import datetime
import pandas as pd
import uuid

# --- Secure API key ---
api_key = st.secrets.get("general", {}).get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()
client = OpenAI(api_key=api_key)

# --- Page setup ---
st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("🌟 Falowen – Your AI Conversation Partner")

# --- Load CSV files with fallback ---
students_file = "students.csv"
try:
    paid_df = pd.read_csv(students_file)
except FileNotFoundError:
    paid_df = pd.DataFrame(columns=["code", "expiry"])

trials_file = "trials.csv"
try:
    trials_df = pd.read_csv(trials_file)
except FileNotFoundError:
    trials_df = pd.DataFrame(columns=["email", "trial_code", "created"])

usage_file = "usage.csv"
try:
    usage_df = pd.read_csv(usage_file, parse_dates=["date"])
except FileNotFoundError:
    usage_df = pd.DataFrame(columns=["user_key", "date", "trial_count", "daily_count"])

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard (Protected) ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Paid Codes")
        new_code = st.text_input("New Paid Code")
        new_expiry = st.date_input("Expiry Date")
        if st.button("➕ Add Paid Code"):
            if new_code and new_code not in paid_df["code"].tolist():
                paid_df.loc[len(paid_df)] = [new_code, new_expiry]
                paid_df.to_csv(students_file, index=False)
                st.success(f"Added paid code {new_code}")
        st.dataframe(paid_df)

        st.subheader("🎫 Trial Codes")
        new_email = st.text_input("New Trial Email")
        if st.button("Issue Trial Code"):
            code_val = uuid.uuid4().hex[:8]
            trials_df.loc[len(trials_df)] = [new_email, code_val, datetime.now()]
            trials_df.to_csv(trials_file, index=False)
            st.success(f"Issued trial code {code_val}")
        st.dataframe(trials_df)
    else:
        st.info("Enter correct teacher password.")
    st.stop()

# --- Practice Mode ---
paid_codes = paid_df["code"].tolist()
access_code = st.text_input("Enter your paid or trial code:")
if not access_code:
    st.info("Please enter your code. If you don't have one, request a trial code below.")
    email_req = st.text_input("Email for trial code")
    if email_req and st.button("Request Trial Code"):
        existing = trials_df[trials_df["email"] == email_req]
        if existing.empty:
            new_code = uuid.uuid4().hex[:8]
            trials_df.loc[len(trials_df)] = [email_req, new_code, datetime.now()]
            trials_df.to_csv(trials_file, index=False)
            st.success(f"Your trial code: {new_code}")
        else:
            st.success(f"Your existing trial code: {existing['trial_code'].iloc[0]}")
    st.stop()

if access_code in paid_codes:
    trial_mode = False
elif access_code in trials_df["trial_code"].tolist():
    trial_mode = True
else:
    st.error("Invalid code.")
    st.stop()

# --- Usage tracking ---
today = datetime.now().date()
mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
if not mask.any():
    usage_df.loc[len(usage_df)] = [access_code, pd.Timestamp(today), 0, 0]
    mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
row_idx = usage_df[mask].index[0]
trial_count = int(usage_df.at[row_idx, "trial_count"])
daily_count = int(usage_df.at[row_idx, "daily_count"])
if trial_mode and trial_count >= 5:
    st.error("🔒 Your 5-message trial has ended.")
    st.stop()
if not trial_mode and daily_count >= 30:
    st.warning("🚫 Daily limit reached.")
    st.stop()

# Increment usage
def increment_usage(is_trial: bool):
    if is_trial:
        usage_df.at[row_idx, "trial_count"] += 1
    else:
        usage_df.at[row_idx, "daily_count"] += 1
    usage_df.to_csv(usage_file, index=False)

# --- Settings ---
with st.expander("⚙️ Settings", expanded=True):
    language = st.selectbox("Language", ["German", "French", "English"])
    level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])

# --- Welcome ---
if trial_mode:
    row = trials_df[trials_df["trial_code"] == access_code]
    display = row["email"].values[0].split("@")[0] if not row.empty else "Learner"
else:
    display = "Student"
st.markdown(f"👋 Hello {display}! Let's chat.")

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []
for m in st.session_state["messages"]:
    st.write(f"{m['role']}: {m['content']}")

# Chat input
msg = st.text_input("Your message here")
if msg:
    increment_usage(trial_mode)
    st.session_state["messages"].append({"role": "user", "content": msg})
    # AI processing goes here
