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
def load_df(path, cols):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame(columns=cols)

paid_df   = load_df("students.csv", ["code","expiry"])
trials_df = load_df("trials.csv", ["email","trial_code","created"])
usage_df  = load_df("usage.csv", ["user_key","date","trial_count","daily_count"])

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard (Protected) ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        # Paid Codes
        st.subheader("🧑‍🏫 Paid Codes Management")
        new_code = st.text_input("New Paid Code")
        new_expiry = st.date_input("Expiry Date")
        if st.button("➕ Add Paid Code"):
            if new_code and new_code not in paid_df["code"].tolist():
                paid_df.loc[len(paid_df)] = [new_code, new_expiry]
                paid_df.to_csv("students.csv", index=False)
                st.success(f"Added paid code {new_code}")
        st.dataframe(paid_df)
        # Trial Codes
        st.subheader("🎫 Trial Codes Management")
        new_email = st.text_input("New Trial Email")
        if st.button("➕ Issue Trial Code"):
            code_val = uuid.uuid4().hex[:8]
            trials_df.loc[len(trials_df)] = [new_email, code_val, datetime.now()]
            trials_df.to_csv("trials.csv", index=False)
            st.success(f"Issued trial code {code_val}")
        st.dataframe(trials_df)
    else:
        st.error("Incorrect password.")
    st.stop()

# --- Practice Mode: Access Control ---
paid_codes  = paid_df["code"].tolist()
trial_codes = trials_df["trial_code"].tolist()
access_code = st.text_input("Enter your paid or trial code:")
if not access_code:
    st.info("Please enter your code or request a trial code below.")
    email_req = st.text_input("Email for trial code request:")
    if email_req and st.button("Request Trial Code"):
        row = trials_df[trials_df.email == email_req]
        if row.empty:
            new_code = uuid.uuid4().hex[:8]
            trials_df.loc[len(trials_df)] = [email_req, new_code, datetime.now()]
            trials_df.to_csv("trials.csv", index=False)
            st.success(f"Your trial code: {new_code}")
        else:
            st.success(f"Your existing trial code: {row.trial_code.iloc[0]}")
    st.stop()
if access_code in paid_codes:
    trial_mode = False
elif access_code in trial_codes:
    trial_mode = True
else:
    st.error("Invalid code.")
    st.stop()

# --- Usage Tracking and Limits ---
today = datetime.now().date()
mask = (usage_df.user_key == access_code) & (usage_df.date == pd.Timestamp(today))
if not mask.any():
    usage_df.loc[len(usage_df)] = [access_code, pd.Timestamp(today), 0, 0]
    mask = (usage_df.user_key == access_code) & (usage_df.date == pd.Timestamp(today))
row_idx = usage_df[mask].index[0]
trial_count = int(usage_df.at[row_idx, 'trial_count'])
daily_count = int(usage_df.at[row_idx, 'daily_count'])
if trial_mode and trial_count >= 5:
    st.error("🔒 Your 5-message trial has ended.")
    st.stop()
if not trial_mode and daily_count >= 30:
    st.warning("🚫 Daily limit reached.")
    st.stop()

def persist_usage(is_trial):
    if is_trial:
        usage_df.at[row_idx, 'trial_count'] += 1
    else:
        usage_df.at[row_idx, 'daily_count'] += 1
    usage_df.to_csv("usage.csv", index=False)

# --- Settings & Role-Play Scenarios ---
with st.expander("⚙️ Settings", expanded=True):
    language = st.selectbox("Language", ["German","French","English"])
    topic    = st.selectbox("Topic", ["Travel","Food","Daily Routine","Work","Free Talk"])
    level    = st.selectbox("Level", ["A1","A2","B1","B2","C1"])
    roleplay = st.checkbox("Role-Play Scenario Mode")
    scenario = None
    if roleplay:
        level_map = {
            'A1': ['Ordering at Cafe','Introducing Yourself','Directions'],
            'A2': ['Hotel Check-In','Market Shopping','Daily Routine'],
            'B1': ['Job Interview','Trip Planning','Hometown Description'],
            'B2': ['Sustainability Debate','Tech Discussion','Art Analysis'],
            'C1': ['Contract Negotiation','News Analysis','Persuasive Speech']
        }
        scenario = st.selectbox("Scenario", level_map[level])

# --- Display Name ---
if trial_mode:
    row = trials_df[trials_df.trial_code == access_code]
    display = row.email.iloc[0].split('@')[0].replace('.', ' ').title() if not row.empty else 'Learner'
else:
    display = 'Student'

# --- Welcome Banner ---
# Use Streamlit native info box for mobile-friendly banner
banner_lines = [
    f"👋 Hello {display}! I'm your AI Speaking Partner 🤖",
    f"**Let's practice your {level} {language} skills!**"
]
if roleplay and scenario:
    banner_lines.append(f"**Scenario:** {scenario}")
banner_lines.append("Start chatting below. 💬")
st.info("

".join(banner_lines))

# --- Chat Interface with Grammar Correction & Scoring ---
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
for msg in st.session_state['messages']:
    with st.chat_message(msg['role']): st.markdown(msg['content'])

user_input = st.chat_input("💬 Type your message here...")
if user_input:
    persist_usage(trial_mode)
    st.session_state['messages'].append({'role':'user','content':user_input})
    st.chat_message('user').markdown(user_input)

    # 1) Grammar Correction
    corr_prompt = (
        f"Correct this {language} sentence to {level}-level grammar and return only the corrected sentence: '{user_input}'"
    )
    corr_resp = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role':'system','content':corr_prompt}]
    )
    corrected = corr_resp.choices[0].message.content.strip()
    if corrected.lower() != user_input.lower():
        st.markdown(f"**Correction:** {corrected}")

    # 2) Tutor Response with Role-Play and Scoring
    sys = f"You are a {level} {language} tutor. Topic: {topic}."
    if roleplay and scenario:
        sys += f" Scenario: {scenario}."
    sys += (
        " After replying naturally, rate the student's message on a scale of 1–10 based on grammar, vocabulary, and clarity, and include 'Score: X'."
    )
    conv = [{'role':'system','content':sys}] + st.session_state['messages']
    ai_resp = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=conv
    )
    ai_text = ai_resp.choices[0].message.content
    st.session_state['messages'].append({'role':'assistant','content':ai_text})
    st.chat_message('assistant').markdown(ai_text)

    # Highlight Score
    m = re.search(r"Score[:\s]+(\d{1,2})", ai_text)
    if m:
        sc = int(m.group(1))
        color = "green" if sc >= 9 else "orange" if sc >= 6 else "red"
        st.markdown(
            f"<div style='display:inline-block;padding:8px;border-radius:8px;background:{color};color:#fff;'>Score: {sc}</div>",
            unsafe_allow_html=True
        )
