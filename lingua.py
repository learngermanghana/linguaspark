import streamlit as st
from openai import OpenAI
import pandas as pd
import uuid
from datetime import datetime

# --- Secure API key ---
api_key = st.secrets.get("general", {}).get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OpenAI API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()
client = OpenAI(api_key=api_key)

# --- Page setup ---
st.set_page_config(page_title="LinguaSpark – Talk to Learn", layout="wide")
st.title("🌟 LinguaSpark – Your AI Conversation Partner")
st.markdown("*v1.1 – Improved by ChatGPT*")

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Helper: Reload DataFrame from CSV ---
def load_csv(filename, columns=None, parse_dates=None):
    try:
        df = pd.read_csv(filename, parse_dates=parse_dates)
    except FileNotFoundError:
        df = pd.DataFrame(columns=columns)
    return df

# --- Helper: Safe GPT call with error handling ---
def safe_gpt_call(prompt, messages):
    try:
        return client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{'role': 'system', 'content': prompt}, *messages]
        ).choices[0].message.content.strip()
    except Exception as e:
        st.error("⚠️ AI error. Please try again later.")
        return "Sorry, something went wrong."

# ============ Teacher Dashboard ============
if mode == "Teacher Dashboard":
    if "TEACHER_PASSWORD" not in st.secrets:
        st.error("Teacher password not set in secrets.toml. Please contact admin.")
        st.stop()

    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets["TEACHER_PASSWORD"]:
        st.subheader("🧑‍🏫 Manage Paid Codes")
        paid_df = load_csv("students.csv", columns=["code", "expiry"])
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

        # Delete paid codes
        st.subheader("🗑️ Delete Paid Codes")
        for idx, row in paid_df.iterrows():
            if st.button(f"Delete {row['code']}", key=f"del_paid_{idx}"):
                paid_df = paid_df[paid_df['code'] != row['code']]
                paid_df.to_csv("students.csv", index=False)
                st.experimental_rerun()

        # Trial codes
        st.subheader("🎫 Trial Codes")
        trials_df = load_csv("trials.csv", columns=["email", "trial_code", "created"])
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

# ============ Practice Mode ============
# Reload CSVs each run for consistency
paid_df = load_csv("students.csv", columns=["code", "expiry"])
paid_users = paid_df["code"].tolist()

# Prompt for code or get trial code by email
code = st.text_input("Enter your access code (paid or trial):")
if not code:
    st.subheader("🎫 Get Your Free Trial Code")
    email = st.text_input("Enter your email:")
    if email:
        trials_df = load_csv("trials.csv", columns=["email", "trial_code", "created"])
        if email in trials_df['email'].values:
            trial_code = trials_df.loc[trials_df['email'] == email, 'trial_code'].values[0]
            st.success(f"Your existing trial code is **{trial_code}**.")
        else:
            trial_code = uuid.uuid4().hex[:8]
            new_row = pd.DataFrame([{
                "email": email,
                "trial_code": trial_code,
                "created": datetime.now().isoformat()
            }])
            trials_df = pd.concat([trials_df, new_row], ignore_index=True)
            trials_df.to_csv("trials.csv", index=False)
            st.success(f"Your trial code is **{trial_code}**. Paste it above to start your 5-message trial.")
    else:
        st.info("Please enter your email to receive a trial code.")
    st.stop()

# --- Determine mode & check expiry for paid codes ---
today = datetime.now().date()
if code in paid_users:
    user_expiry = paid_df.set_index("code").at[code, "expiry"]
    if pd.to_datetime(user_expiry).date() < today:
        st.error("Your code has expired. Please contact your teacher.")
        st.stop()
    trial_mode = False
elif code:
    trials_df = load_csv("trials.csv", columns=["email", "trial_code", "created"])
    if code in trials_df['trial_code'].values:
        trial_mode = True
    else:
        st.error("Invalid code. Please use a valid paid or trial code.")
        st.stop()
else:
    st.stop()

# --- Persist Usage ---
USAGE_FILE = "usage.csv"
usage_df = load_csv(USAGE_FILE, columns=['user_key', 'date', 'trial_count', 'daily_count'], parse_dates=['date'])
user_key = code
mask = (usage_df['user_key'] == user_key) & (usage_df['date'] == pd.Timestamp(today))
if not mask.any():
    usage_df.loc[len(usage_df)] = [user_key, pd.Timestamp(today), 0, 0]
    mask = (usage_df['user_key'] == user_key) & (usage_df['date'] == pd.Timestamp(today))
row_idx = usage_df[mask].index[0]
trial_count = int(usage_df.at[row_idx, 'trial_count'])
daily_count = int(usage_df.at[row_idx, 'daily_count'])
if trial_mode:
    st.warning(f"Trial usage: {trial_count}/5 messages used. {5 - trial_count} remaining.")
    if trial_count >= 5:
        st.error("🔒 Trial over. Please pay to continue.")
        st.stop()
else:
    st.info(f"Today: {daily_count}/30 messages used.")
    if daily_count >= 30:
        st.warning("🚫 Daily limit reached.")
        st.stop()

# --- Settings ---
with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Language", ["German", "French", "English"])
    topic = st.selectbox("Topic", ["Travel", "Food", "Daily Routine", "Work", "Free Talk"])
    level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])
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
    st.markdown("---")
    st.markdown("**💡 Tips:**\n- Click '🧹 Clear Chat' to restart.\n- Click '⬇️ Download Chat' to save.")

# --- Welcome ---
name = code
st.markdown(f"<div style='padding:16px;border-radius:12px;background:#e0f7fa;'>👋 Hello {name}! Let's chat (A1–C1). Type your message below.</div>", unsafe_allow_html=True)

# --- Chat logic ---
if 'messages' not in st.session_state:
    st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m['role']):
        st.markdown(m['content'])

user_input = st.chat_input("Your message...")

if user_input:
    # Update usage
    if trial_mode:
        usage_df.at[row_idx, 'trial_count'] = trial_count + 1
    else:
        usage_df.at[row_idx, 'daily_count'] = daily_count + 1
    usage_df.to_csv(USAGE_FILE, index=False)

    # Show user
    st.session_state.messages.append({'role': 'user', 'content': user_input})
    st.chat_message('user').markdown(user_input)

    # Correction
    correction_prompt = (
        f"You are a language tutor. Please correct the following sentence "
        f"to match level {level} in {language}. Only show the corrected sentence. "
        f"Sentence: {user_input}"
    )
    corr = safe_gpt_call(correction_prompt, [])
    if corr.lower() != user_input.lower():
        st.markdown(f"**Correction:** {corr}")

    # Tutor reply
    tutor_prompt = f"Tutor {level}, topic {topic}" + (f" scenario {scenario}" if scenario_mode else "") + " rate with Score: X."
    ai = safe_gpt_call(tutor_prompt, st.session_state.messages)
    st.session_state.messages.append({'role': 'assistant', 'content': ai})
    st.chat_message('assistant').markdown(ai)

# --- Utilities ---
st.markdown("---")
cols = st.columns(2)
with cols[0]:
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()
with cols[1]:
    if st.session_state.messages:
        chat_history = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("⬇️ Download Chat", chat_history, file_name=f"{code}_linguaspark.txt")

# --- Footer ---
st.markdown("<small><i>Made with ❤️ by Learn Language Education Academy</i></small>", unsafe_allow_html=True)
