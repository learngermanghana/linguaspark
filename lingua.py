import streamlit as st
from openai import OpenAI
import io
import re
from datetime import datetime
import pandas as pd
import sqlite3

# --- Page setup ---
st.set_page_config(page_title="LinguaSpark – Talk to Learn", layout="wide")
st.title("🌟 LinguaSpark – Your AI Conversation Partner")

# --- Secure API key ---
api_key = st.secrets.get("general", {}).get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OpenAI API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()
client = OpenAI(api_key=api_key)

# --- SQLite setup ---
conn = sqlite3.connect('students.db', check_same_thread=False)
c = conn.cursor()
c.execute(
    """
    CREATE TABLE IF NOT EXISTS students (
        code TEXT PRIMARY KEY,
        expiry TEXT
    )
    """
)
conn.commit()

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("general", {}).get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Manage Student Access (SQLite)")
        df = pd.read_sql_query("SELECT code, expiry FROM students", conn)
        st.dataframe(df)

        new_code = st.text_input("New Student Code")
        new_expiry = st.date_input("Expiry Date")
        if st.button("➕ Add Code"):
            if new_code:
                try:
                    c.execute(
                        "INSERT INTO students (code, expiry) VALUES (?, ?)",
                        (new_code, new_expiry.strftime("%Y-%m-%d"))
                    )
                    conn.commit()
                    st.success(f"✅ Added code {new_code}")
                except sqlite3.IntegrityError:
                    st.warning("⚠️ Code already exists.")
            else:
                st.warning("⚠️ Please enter a valid code.")
    else:
        st.info("Enter correct password to access the dashboard.")
    st.stop()

# --- Practice Mode ---
def load_users():
    df = pd.read_sql_query("SELECT code, expiry FROM students", conn)
    return {row['code']: row['expiry'] for _, row in df.iterrows()}

paid_users = load_users()

# Initialize session counters
if 'trial_messages' not in st.session_state:
    st.session_state.trial_messages = 0
if 'daily_count' not in st.session_state:
    st.session_state.daily_count = 0
if 'usage_date' not in st.session_state:
    st.session_state.usage_date = datetime.now().date()

# Load persistent trial count
qp = st.query_params
if 'trial' in qp:
    try:
        st.session_state.trial_messages = int(qp['trial'][0])
    except:
        pass

# Reset daily count on new day
today = datetime.now().date()
if st.session_state.usage_date != today:
    st.session_state.usage_date = today
    st.session_state.daily_count = 0

# Access control: code or trial
trial_mode = False
code = st.text_input("Enter access code (or leave blank for a 5-message free trial):")
if code:
    if code not in paid_users:
        st.warning("🔒 Invalid code. Please contact the tutor.")
        st.stop()
    expiry = datetime.strptime(paid_users[code], "%Y-%m-%d").date()
    days_left = (expiry - today).days
    if days_left < 0:
        st.error("🔒 Access expired. Please renew your subscription.")
        st.stop()
    st.success(f"✅ Premium Access: {days_left} day(s) remaining.")
else:
    trial_mode = True
    if st.session_state.trial_messages >= 5:
        st.error(
            "🔒 Free trial ended. Please pay 100 GHS for 60 days full access.\n"
            "💳 MTN Momo: 233245022743 (Asadu Felix)\n"
            "📞 WhatsApp proof: 233205706589"
        )
        st.stop()
    st.info(f"🎁 Free trial: {5 - st.session_state.trial_messages} messages left")

# Paid users daily message limit
if not trial_mode and st.session_state.daily_count >= 30:
    st.warning("🚫 Daily message limit reached. Please try again tomorrow.")
    st.stop()

# --- Practice Settings ---
if mode == "Practice":
    with st.sidebar:
        st.header("Settings")
        language = st.selectbox("Language", ["German", "French", "English"])
        topic = st.selectbox("Topic", ["Travel", "Food", "Daily Routine", "Work", "Free Talk"])
        level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])

# --- Encouragement Banner ---
name = code.title() if code else "there"
st.markdown(
    f"<div style='padding:16px; border-radius:12px; background:#e0f7fa;'>👋 Hello {name}! I'm your AI Speaking Partner 🤖<br><br>"
    "We can chat at any level from <b>A1 to C1</b> 📘.<br>"
    "Choose your level, select a topic, and start chatting or upload your voice 🎤.<br><br>"
    "I'm here to correct your mistakes and boost your confidence. Let's begin! 💬</div>",
    unsafe_allow_html=True
)

# --- Audio Upload ---
st.subheader("📄 Upload Audio (WAV/MP3/M4A)")
audio = st.file_uploader("Upload voice", type=["wav", "mp3", "m4a"], key="audio_upload")
user_input = None
if audio:
    buf = audio.read()
    stream = io.BytesIO(buf)
    stream.name = audio.name
    user_input = client.audio.transcriptions.create(
        model="whisper-1",
        file=stream,
        language={"German": "de", "French": "fr", "English": "en"}[language]
    ).text
    st.success("🚣️ Transcribed:")
    st.write(user_input)

# --- Chat History & Input ---
if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

user_input = st.chat_input("💬 Type your message here...", key="chat_input")
if user_input:
    if trial_mode:
        st.session_state.trial_messages += 1
        st.experimental_set_query_params(trial=st.session_state.trial_messages)
    else:
        st.session_state.daily_count += 1
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    system_prompt = f"""
You are a tutor for a {level} student.
Language: {language}, Topic: {topic}.

- Reply naturally in {language}, using {level}-appropriate vocabulary and grammar.
- If the student's message contains any grammar mistakes, provide a second paragraph explaining each correction in English, prefaced with **Correction:**.
- Keep responses concise and appropriate for the student's proficiency level.
- After replying, rate the student's message on a scale from 1 to 10 based on grammar, vocabulary, and clarity, and write `Score: X` on a new line.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}, *st.session_state.messages]
    )
    ai = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ai})
    parts = ai.split("\n\n")
    reply = parts[0]
    correction = "\n\n".join(parts[1:]) if len(parts)>1 else None
    st.chat_message("assistant").markdown(reply)
    if correction:
        st.markdown(f"**Correction:** {correction}")
    match = re.search(r"Score[:\s]+(\d{1,2})", ai)
    if match:
        sc = int(match.group(1))
        clr = "green" if sc >= 9 else "orange" if sc >= 6 else "red"
        st.markdown(
            f"<div style='padding:8px; border-radius:10px; background-color:{clr}; color:white; display:inline-block;'>Score: {sc}</div>",
            unsafe_allow_html=True
        )
