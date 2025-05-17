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
    page_title="Falowen – Your AI Conversation Partner", layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("🌟 Falowen – Your AI Conversation Partner")

# --- Load data files (handle missing) ---
students_file = "students.csv"
try:
    paid_df = pd.read_csv(students_file)
except FileNotFoundError:
    paid_df = pd.DataFrame(columns=["code","expiry"])
trials_file = "trials.csv"
try:
    trials_df = pd.read_csv(trials_file)
except FileNotFoundError:
    trials_df = pd.DataFrame(columns=["email","trial_code","created"])
usage_file = "usage.csv"
try:
    usage_df = pd.read_csv(usage_file, parse_dates=['date'])
except FileNotFoundError:
    usage_df = pd.DataFrame(columns=['user_key','date','trial_count','daily_count'])

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard (Protected) ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        # Paid Codes Management
        st.subheader("🧑‍🏫 Manage Paid Codes")
        new_code = st.text_input("New Paid Code:")
        new_expiry = st.date_input("Expiry Date:")
        if st.button("➕ Add Paid Code"):
            if new_code and new_code not in paid_df['code'].values:
                paid_df.loc[len(paid_df)] = [new_code, new_expiry]
                paid_df.to_csv(students_file, index=False)
                st.success(f"✅ Added paid code {new_code}")
            else:
                st.warning("Code exists or empty.")
        st.subheader("📋 Paid Codes List")
        st.dataframe(paid_df)
        # Delete Paid Codes
        st.subheader("🗑️ Delete Paid Codes")
        for idx, row in paid_df.iterrows():
            if st.button(f"Delete {row['code']}", key=f"del_paid_{idx}"):
                paid_df = paid_df[paid_df['code'] != row['code']]
                paid_df.to_csv(students_file, index=False)
                st.experimental_rerun()
        # Trial Codes Management
        st.subheader("🎫 Trial Codes List")
        st.dataframe(trials_df)
        # Delete Trial Codes
        st.subheader("🗑️ Delete Trial Codes")
        for idx, row in trials_df.iterrows():
            if st.button(f"Delete {row['trial_code']}", key=f"del_trial_{idx}"):
                trials_df = trials_df[trials_df['trial_code'] != row['trial_code']]
                trials_df.to_csv(trials_file, index=False)
                st.experimental_rerun()
    else:
        st.info("Enter correct teacher password to access this page.")
    st.stop()

# --- Practice Mode ---
# Prepare paid codes list
paid_users = paid_df['code'].tolist()

# Prompt for access code or email trial
code = st.text_input("Enter your access code (paid or trial):")
if not code:
    st.subheader("🎫 Get Your Free Trial Code")
    email = st.text_input("Enter your email:")
    if email:
        if email in trials_df['email'].values:
            trial_code = trials_df.loc[trials_df['email']==email, 'trial_code'].values[0]
        else:
            trial_code = uuid.uuid4().hex[:8]
            trials_df.loc[len(trials_df)] = [email, trial_code, datetime.now().isoformat()]
            trials_df.to_csv(trials_file, index=False)
        st.success(f"Your trial code is **{trial_code}**. Paste it above to start your 5-message trial.")
    else:
        st.info("Please enter your email to receive a trial code.")
    st.stop()

# Determine mode and validate code
trial_mode = False
if code in paid_users:
    trial_mode = False
elif code in trials_df['trial_code'].values:
    trial_mode = True
else:
    st.error("Invalid code. Enter a paid code or a valid trial code.")
    st.stop()

# --- Usage Persistence & Limits ---
today = datetime.now().date()
mask = (usage_df['user_key']==code)&(usage_df['date']==pd.Timestamp(today))
if not mask.any():
    usage_df.loc[len(usage_df)] = [code, pd.Timestamp(today), 0, 0]
    mask = (usage_df['user_key']==code)&(usage_df['date']==pd.Timestamp(today))
row_idx = usage_df[mask].index[0]
trial_count = int(usage_df.at[row_idx,'trial_count'])
daily_count = int(usage_df.at[row_idx,'daily_count'])
# Enforce limits
if trial_mode and trial_count>=5:
    st.error("🔒 Your 5-message trial has ended.")
    st.markdown(
        "To continue using **Falowen**, pay **100 GHS** for a 60-day plan via Momo: 233245022743."
    )
    st.stop()
if not trial_mode and daily_count>=30:
    st.warning("🚫 Daily limit reached.")
    st.markdown(
        "Upgrade for **100 GHS** (60 days unlimited) via Momo: 233245022743."
    )
    st.stop()

# --- Settings (Mobile-Friendly) ---
with st.expander("⚙️ Settings", expanded=True):
    language = st.selectbox("Language", ["German","French","English"])
    topic = st.selectbox("Topic", ["Travel","Food","Daily Routine","Work","Free Talk"])
    level = st.selectbox("Level", ["A1","A2","B1","B2","C1"])
    scenario_mode = st.checkbox("Role-Play Scenario")
    scenarios_map = {
        'A1':['Ordering at Cafe','Introducing','Directions'],
        'A2':['Hotel','Market','Routine'],
        'B1':['Interview','Trip','Hometown'],
        'B2':['Sustainability','Tech','Art'],
        'C1':['Contract','News','Debate']
    }
    scenario = st.selectbox("Scenario", scenarios_map[level]) if scenario_mode else None

# --- Welcome Banner & Chat ---
if trial_mode:
    row = trials_df[trials_df['trial_code']==code]
    display_name = row['email'].values[0].split('@')[0].replace('.', ' ').title() if not row.empty else 'Learner'
else:
    display_name = 'Student'

st.markdown(
    f"""
    <div style='padding:16px;border-radius:12px;background:#e0f7fa;'>
    👋 Hello {display_name}! Chat A1–C1 🤖<br>
    Start by typing or uploading your voice! 💬
    </div>
    """,
    unsafe_allow_html=True
)

# Chat history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
for msg in st.session_state['messages']:
    with st.chat_message(msg['role']): st.markdown(msg['content'])

# Chat input & processing
user_input = st.chat_input("Your message...")
if user_input:
    # update counts
    usage_df.at[row_idx,'trial_count'] = trial_count + (1 if trial_mode else 0)
    usage_df.at[row_idx,'daily_count'] = daily_count + (0 if trial_mode else 1)
    usage_df.to_csv(usage_file,index=False)
    # user message
    st.session_state['messages'].append({'role':'user','content':user_input})
    st.chat_message('user').markdown(user_input)
    # grammar correction
    corr = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{'role':'system','content':f"Correct this {language} sentence to {level} grammar: '{user_input}'"}]
    ).choices[0].message.content.strip()
    if corr.lower()!=user_input.lower(): st.markdown(f"**Correction:** {corr}")
    # tutor response
    tutor_prompt = f"You are a {level} tutor. Topic: {topic}. Converse in {language}" + (f" about {scenario}." if scenario_mode else ".") + " After, rate with 'Score: X'."
    ai = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{'role':'system','content':tutor_prompt}, *st.session_state['messages']]
    ).choices[0].message.content
    st.session_state['messages'].append({'role':'assistant','content':ai})
    st.chat_message('assistant').markdown(ai)
