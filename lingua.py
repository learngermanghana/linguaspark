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
cursor = conn.cursor()
cursor.execute(
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
    password = st.text_input("🔐 Teacher Password:", type="password")
    teacher_password = st.secrets.get("general", {}).get("TEACHER_PASSWORD", "admin123")
    if password == teacher_password:
        st.subheader("🧑‍🏫 Manage Student Access (SQLite)")
        df = pd.read_sql_query("SELECT code, expiry FROM students", conn)
        st.dataframe(df)

        new_code = st.text_input("New Student Code")
        new_expiry = st.date_input("Expiry Date")
        if st.button("➕ Add Code"):
            if new_code:
                try:
                    cursor.execute(
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

# --- Practice Mode: helper to load users ---
def load_users():
    df = pd.read_sql_query("SELECT code, expiry FROM students", conn)
    return {row['code']: row['expiry'] for _, row in df.iterrows()}

paid_users = load_users()

# --- Session state counters ---
if 'trial_messages' not in st.session_state:
    st.session_state.trial_messages = 0
if 'daily_count' not in st.session_state:
    st.session_state.daily_count = 0
if 'usage_date' not in st.session_state:
    st.session_state.usage_date = datetime.now().date()

# Load persistent trial count from URL params
params = st.experimental_get_query_params()
if 'trial' in params:
    try:
        st.session_state.trial_messages = int(params['trial'][0])
    except ValueError:
        pass

# Reset daily count if a new day has started
today = datetime.now().date()
if st.session_state.usage_date != today:
    st.session_state.usage_date = today
    st.session_state.daily_count = 0

# --- Access control ---
trial_mode = False
access_code = st.text_input("Enter access code (or leave blank for a 5-message free trial):")
if access_code:
    if access_code not in paid_users:
        st.warning("🔒 Invalid code. Please contact the tutor.")
        st.stop()
    expiry_date = datetime.strptime(paid_users[access_code], "%Y-%m-%d").date()
    days_left = (expiry_date - today).days
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

# Enforce daily limit for paid users
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
else:
    language = topic = level = None

# --- Encouragement Banner ---
student_name = access_code.title() if access_code else "there"
st.markdown(
    f"<div style='padding:16px; border-radius:12px; background:#e0f7fa;'>"
    f"👋 Hello {student_name}! I'm your AI Speaking Partner 🤖<br><br>"
    "We can chat at any level from <b>A1 to C1</b> 📘.<br>"
    "Choose your level, select a topic, and start chatting or upload your voice 🎤.<br><br>"
    "I'm here to correct your mistakes and boost your confidence. Let's begin! 💬"  
    "</div>",
    unsafe_allow_html=True
)

# --- Audio Upload ---
st.subheader("📄 Upload Audio (WAV/MP3/M4A)")
audio_file = st.file_uploader("Upload voice", type=["wav", "mp3", "m4a"], key="audio_upload")
if audio_file:
    audio_bytes = audio_file.read()
    audio_stream = io.BytesIO(audio_bytes)
    audio_stream.name = audio_file.name
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_stream,
        language={"German": "de", "French": "fr", "English": "en"}[language]
    ).text
    st.success("🚣️ Transcribed:")
    st.write(transcript)
    chat_input = transcript
else:
    chat_input = st.chat_input("💬 Type your message here...", key="chat_input")

# --- Chat History & Interaction ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Process new input
if chat_input:
    # Update counters
    if trial_mode:
        st.session_state.trial_messages += 1
        st.experimental_set_query_params(trial=st.session_state.trial_messages)
    else:
        st.session_state.daily_count += 1

    # Record user message
    st.session_state.messages.append({"role": "user", "content": chat_input})
    st.chat_message("user").markdown(chat_input)

    # Build system prompt
    system_prompt = (
        f"You are a tutor for a {level} student.\n"
        f"Language: {language}, Topic: {topic}.\n\n"
        "- Reply naturally in {language}, using {level}-appropriate vocabulary and grammar.\n"
        "- If the student's message contains any grammar mistakes, provide a second paragraph explaining each correction in English, prefaced with **Correction**:.\n"
        "- Keep responses concise and appropriate for the student's proficiency level.\n"
        "- After replying, rate the student's message on a scale from 1 to 10 based on grammar, vocabulary, and clarity, and write `Score: X` on a new line."
    )

    # Fetch AI response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}, *st.session_state.messages]
    )
    ai_content = response.choices[0].message.content

    # Display AI response
    st.session_state.messages.append({"role": "assistant", "content": ai_content})  
    parts = ai_content.split("\n\n")
    reply = parts[0]
    correction = "\n\n".join(parts[1:]) if len(parts) > 1 else None

    st.chat_message("assistant").markdown(reply)
    if correction:
        st.markdown(f"**Correction:** {correction}")

    # Extract and show score
    match = re.search(r"Score[:\s]+(\d{1,2})", ai_content)
    if match:
        score = int(match.group(1))
        color = "green" if score >= 9 else "orange" if score >= 6 else "red"
        st.markdown(
            f"<div style='padding:8px; border-radius:10px; background-color:{color}; color:white;'"
            f" display:inline-block;'>Score: {score}</div>",
            unsafe_allow_html=True
        )
