import streamlit as st
from openai import OpenAI
import io
import re
from datetime import datetime
import pandas as pd

# --- Secure API key ---
api_key = st.secrets.get("general", {}).get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OpenAI API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()

client = OpenAI(api_key=api_key)

# --- Page setup ---
st.set_page_config(page_title="LinguaSpark – Talk to Learn", layout="wide")
st.title("🌟 LinguaSpark – Your AI Conversation Partner")

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Manage Student Access")
        try:
            user_df = pd.read_csv("students.csv")
        except FileNotFoundError:
            user_df = pd.DataFrame(columns=["code","expiry"])
        new_code = st.text_input("New Student Code")
        new_expiry = st.date_input("Expiry Date")
        if st.button("➕ Add Code"):
            if new_code and new_code not in user_df['code'].values:
                new_row = pd.DataFrame([[new_code, new_expiry]], columns=['code','expiry'])
                user_df = pd.concat([user_df, new_row], ignore_index=True)
                user_df.to_csv("students.csv", index=False)
                st.success(f"✅ Added code {new_code}")
            else:
                st.warning("Code exists or empty.")
        st.subheader("📋 Current Students")
        st.dataframe(user_df)
    else:
        st.info("Enter correct password to access.")
    st.stop()

# --- Practice Mode ---
# Load paid users
def load_users():
    try:
        df = pd.read_csv("students.csv")
        return {r['code']: r['expiry'] for _, r in df.iterrows()}
    except:
        return {}
paid_users = load_users()

trial_mode = False
code = st.text_input("Enter access code (or leave blank for 5 free messages):")
if code:
    if code not in paid_users:
        st.warning("🔒 Invalid code.")
        st.stop()
    expiry = datetime.strptime(paid_users[code], "%Y-%m-%d").date()
    days_left = (expiry - datetime.now().date()).days
    if days_left < 0:
        st.error("🔒 Access expired.")
        st.stop()
    st.success(f"✅ {days_left} day(s) remaining")
else:
    trial_mode = True
    st.session_state.trial_messages = st.session_state.get('trial_messages', 0)
    if st.session_state.trial_messages >= 5:
        st.error("🔒 Trial ended. Pay 100 GHS for 60 days. Momo:233245022743 (Asadu Felix). Proof WhatsApp:233205706589")
        st.stop()
    st.info(f"🎁 Trial messages left: {5 - st.session_state.trial_messages}")

# Reset daily count
today = datetime.now().date()
if st.session_state.get('usage_date') != today:
    st.session_state.usage_date = today
    st.session_state.daily_count = 0
if not trial_mode and st.session_state.daily_count >= 30:
    st.warning("🚫 Daily limit reached.")
    st.stop()

# --- Practice Settings ---
if mode == "Practice":
    with st.sidebar:
        st.header("Settings")
        language = st.selectbox("Language", ["German", "French", "English"])
        topic = st.selectbox("Topic", ["Travel", "Food", "Daily Routine", "Work", "Free Talk"])
        level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])

# --- Welcoming & Encouragement Message ---
name = code.title() if code else "there"
st.markdown(
    f"""
    <div style='padding:16px; border-radius:12px; background:#e0f7fa;'>
    👋 Hello {name}! I'm your AI Speaking Partner 🤖<br><br>
    We can converse at any level from <b>A1</b> to <b>C1</b>.<br>
    Choose your level, select a topic, and start chatting or upload your voice to get instant feedback.<br><br>
    Feel free to ask me anything—I'm here to help you learn, correct your mistakes, and build confidence. Let's begin! 💬
    </div>
    """, unsafe_allow_html=True)

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
    st.success("Transcribed:")
    st.write(user_input)

# --- Welcome Message ---
name = code.title() if code else "there"
st.markdown(
    f"<div style='padding:12px; border-radius:12px; background:#f0f8ff;'>👋 Hello {name}! Chat A1–C1 🤖</div>",
    unsafe_allow_html=True
)

# --- Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# --- Chat Input ---
user_input = st.chat_input("💬 Type your message here...", key="chat_input")

# --- Process Input ---
if user_input:
    if trial_mode:
        st.session_state.trial_messages += 1
    else:
        st.session_state.daily_count += 1

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)

    # System prompt aligned correctly
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

    # Display reply
    parts = ai.split("\n\n")
    reply = parts[0]
    correction = "\n\n".join(parts[1:]) if len(parts) > 1 else None
    st.chat_message("assistant").markdown(reply)
    if correction:
        st.markdown(f"**Correction:** {correction}")

    # Score badge
    m = re.search(r"Score[:\s]+(\d{1,2})", ai)
    if m:
        sc = int(m.group(1))
        clr = "green" if sc >= 9 else "orange" if sc >= 6 else "red"
        st.markdown(
            f"<div style='padding:8px; border-radius:10px; background-color:{clr}; color:white; display:inline-block;'>Score: {sc}</div>",
            unsafe_allow_html=True
        )
