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
    st.error("❌ OpenAI API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()
client = OpenAI(api_key=api_key)

# --- Page setup ---
st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="wide",
    initial_sidebar_state="collapsed"
)  # Collapse sidebar by default for mobile-friendly view
st.title("🌟 Falowen – Your AI Conversation Partner")

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Manage Paid Codes")
        try:
            paid_df = pd.read_csv("students.csv")
        except FileNotFoundError:
            paid_df = pd.DataFrame(columns=["code","expiry"])
        new_code = st.text_input("New Student Code:")
        new_expiry = st.date_input("Expiry Date:")
        if st.button("➕ Add Paid Code"):
            if new_code and new_code not in paid_df['code'].values:
                paid_df.loc[len(paid_df)] = [new_code, new_expiry]
                paid_df.to_csv("students.csv", index=False)
                st.success(f"✅ Added paid code {new_code}")
            else:
                st.warning("Code exists or empty.")
        st.subheader("📋 Paid Codes List")
        st.dataframe(paid_df)
        # delete paid codes
        st.subheader("🗑️ Delete Paid Codes")
        for idx, row in paid_df.iterrows():
            if st.button(f"Delete {row['code']}", key=f"del_paid_{idx}"):
                paid_df = paid_df[paid_df['code'] != row['code']]
                paid_df.to_csv("students.csv", index=False)
                st.experimental_rerun()

        # trial codes
        st.subheader("🎫 Trial Codes")
        try:
            trials_df = pd.read_csv("trials.csv")
        except FileNotFoundError:
            trials_df = pd.DataFrame(columns=["email","trial_code","created"])
        st.dataframe(trials_df)
        st.subheader("🗑️ Delete Trial Codes")
        for idx, row in trials_df.iterrows():
            if st.button(f"Delete {row['trial_code']}", key=f"del_trial_{idx}"):
                trials_df = trials_df[trials_df['trial_code'] != row['trial_code']]
                trials_df.to_csv("trials.csv", index=False)
                st.experimental_rerun()
    else:
        st.info("Enter correct teacher password.")
    st.stop()

# --- Practice Mode ---
# load paid users
try:
    paid_users = pd.read_csv("students.csv")["code"].tolist()
except FileNotFoundError:
    paid_users = []

# prompt for code or email to get trial code
code = st.text_input("Enter your access code (paid or trial):")
if not code:
    st.subheader("🎫 Get Your Free Trial Code")
    email = st.text_input("Enter your email:")
    if email:
        try:
            trials_df = pd.read_csv("trials.csv")
        except FileNotFoundError:
            trials_df = pd.DataFrame(columns=["email","trial_code","created"])
        if email in trials_df['email'].values:
            trial_code = trials_df.loc[trials_df['email']==email, 'trial_code'].values[0]
        else:
            trial_code = uuid.uuid4().hex[:8]
            trials_df.loc[len(trials_df)] = [email, trial_code, datetime.now().isoformat()]
            trials_df.to_csv("trials.csv", index=False)
        # Display code in single line f-string to avoid unterminated literal
        st.success(f"Your trial code is **{trial_code}**. Paste it above to start your 5-message trial.")
    else:
        st.info("Please enter your email to receive a trial code.")
    st.stop()

# determine mode
if code in paid_users:
    trial_mode = False
elif code:
    try:
        trials_df
    except NameError:
        trials_df = pd.read_csv("trials.csv")
    if code in trials_df['trial_code'].values:
        trial_mode = True
    else:
        st.error("Invalid code. Please use a valid paid or trial code.")
        st.stop()
else:
    # should not reach here
    st.stop()

# --- Persist Usage ---
USAGE_FILE = "usage.csv"
try:
    usage_df = pd.read_csv(USAGE_FILE, parse_dates=['date'])
except FileNotFoundError:
    usage_df = pd.DataFrame(columns=['user_key','date','trial_count','daily_count'])
user_key = code
today = datetime.now().date()
mask = (usage_df['user_key']==user_key)&(usage_df['date']==pd.Timestamp(today))
if not mask.any():
    usage_df.loc[len(usage_df)] = [user_key, pd.Timestamp(today), 0, 0]
    mask = (usage_df['user_key']==user_key)&(usage_df['date']==pd.Timestamp(today))
row_idx = usage_df[mask].index[0]
trial_count = int(usage_df.at[row_idx,'trial_count'])
daily_count = int(usage_df.at[row_idx,'daily_count'])
# Enforce limits and prompt payment
if trial_mode and trial_count >= 5:
    st.error("🔒 Your 5-message trial has ended.")
    st.markdown(
        """
        To continue using **Falowen**, please pay **100 GHS** for a 60-day plan via Mobile Money:<br>
        • Momo: **233245022743** (Asadu Felix) <button onclick="navigator.clipboard.writeText('233245022743')">Copy Number</button><br>
        • Confirm payment: <a href="https://api.whatsapp.com/send?phone=233205706589&text=I%20have%20paid%20100%20GHS%20for%2060-day%20plan">WhatsApp</a>
        """,
        unsafe_allow_html=True
    )
    st.stop()
if not trial_mode and daily_count >= 30:
    st.warning("🚫 You’ve reached your daily limit of 30 messages.")
    st.markdown(
        """
        Need more? Upgrade to the paid plan: **100 GHS** for 60 days unlimited access:<br>
        • Momo: **233245022743** (Asadu Felix) <button onclick="navigator.clipboard.writeText('233245022743')">Copy Number</button><br>
        • After payment, re-enter your paid code above to unlock access.<br>
        • Confirm via WhatsApp: <a href="https://api.whatsapp.com/send?phone=233205706589&text=I%20have%20paid%20100%20GHS">Click here</a>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# --- Settings (Mobile-Friendly) ---
# Use a collapsible expander instead of sidebar for mobile UX
with st.expander("⚙️ Settings", expanded=True):
    language = st.selectbox("Language", ["German","French","English"])
    topic = st.selectbox("Topic", ["Travel","Food","Daily Routine","Work","Free Talk"])
    level = st.selectbox("Level", ["A1","A2","B1","B2","C1"])
    scenario_mode = st.checkbox("Role-Play Scenario")
    if scenario_mode:
        scenarios = {
            'A1': ['Ordering at Cafe', 'Introducing', 'Directions'],
            'A2': ['Hotel', 'Market', 'Routine'],
            'B1': ['Interview', 'Trip', 'Hometown'],
            'B2': ['Sustainability', 'Tech', 'Art'],
            'C1': ['Contract', 'News', 'Debate']
        }[level]
        scenario = st.selectbox("Scenario", scenarios)

