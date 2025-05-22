import streamlit as st
from openai import OpenAI
from datetime import datetime
import pandas as pd
import uuid
import tempfile
import io
from gtts import gTTS

# ---- API and data setup ----
api_key = st.secrets.get("general", {}).get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()
client = OpenAI(api_key=api_key)

st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS to hide menu, reaction widgets, and style chat ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Hide Streamlit reaction widgets */
    .st-emotion, .st-emotion-actions, .st-emotion-cache {visibility: hidden !important;}
    .stChatMessage.user {background: #e1f5fe; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    .stChatMessage.assistant {background: #f0f4c3; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    </style>
""", unsafe_allow_html=True)

st.header("🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor!")
st.image("https://cdn.pixabay.com/photo/2013/07/13/12/47/student-146981_960_720.png", width=100)
st.markdown("> Practice your speaking or writing. Get simple AI feedback and audio answers!")

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

# --- File paths ---
students_file = "students.csv"
trials_file = "trials.csv"
usage_file = "usage.csv"

# --- Data helpers ---
def save_df(df, path):
    df.to_csv(path, index=False)

def load_df(path, cols, date_cols=None):
    try:
        return pd.read_csv(path, parse_dates=date_cols)
    except FileNotFoundError:
        return pd.DataFrame(columns=cols)

# Load datasets
paid_df = load_df(students_file, ["code", "expiry"], date_cols=["expiry"])
paid_df["expiry"] = pd.to_datetime(paid_df["expiry"], errors="coerce")
trials_df = load_df(trials_file, ["email", "trial_code", "created"], date_cols=["created"])
usage_df = load_df(usage_file, ["user_key", "date", "trial_count", "daily_count"], date_cols=["date"])

# --- Sidebar Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Manage Paid Codes")
        with st.form("add_paid"):  # Add new paid code
            c1, c2 = st.columns([2, 2])
            new_code = c1.text_input("New Paid Code")
            new_expiry = c2.date_input("Expiry Date", datetime.now())
            if st.form_submit_button("Add Paid Code"):
                paid_df.loc[len(paid_df)] = [new_code, pd.to_datetime(new_expiry)]
                save_df(paid_df, students_file)
                st.success(f"Added paid code {new_code}")
        st.markdown("---")
        st.subheader("🎫 Manage Trial Codes")
        with st.form("add_trial"):  # Issue new trial code
            email = st.text_input("Email for Trial Code")
            if st.form_submit_button("Issue Trial Code"):
                code_val = uuid.uuid4().hex[:8]
                trials_df.loc[len(trials_df)] = [email, code_val, datetime.now()]
                save_df(trials_df, trials_file)
                st.success(f"Issued trial code {code_val}")
    else:
        st.info("Enter correct teacher password.")
    st.stop()

# --- Practice Mode ---
language = st.selectbox(
    "🌍 Choose your language",
    ["German", "French", "English", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic"]
)
with st.expander("ℹ️ How to Use / Get Access"):
    st.markdown(
        """
**Trial Access:** Enter your email for a free trial code.

**Paid Access:** Enter your paid code. Contact tutor on WhatsApp after payment.
        """
    )

# Access control
access_code = st.text_input("🔐 Enter your paid or trial code:")
if not access_code:
    st.info("Don't have a code? Enter your email below to request a free trial code.")
    email_req = st.text_input("Email for trial code")
    if email_req and st.button("Request Trial Code"):
        existing = trials_df[trials_df["email"] == email_req]
        if existing.empty:
            new_code = uuid.uuid4().hex[:8]
            trials_df.loc[len(trials_df)] = [email_req, new_code, datetime.now()]
            save_df(trials_df, trials_file)
            st.success(f"Your trial code: {new_code}")
        else:
            st.success(f"Your existing trial code: {existing['trial_code'].iloc[0]}")
    st.stop()

# Determine trial vs paid mode
trial_mode = False
if access_code in paid_df["code"].tolist():
    trial_mode = False
elif access_code in trials_df["trial_code"].tolist():
    trial_mode = True

# Usage tracking
today = datetime.now().date()
mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
if not mask.any():
    usage_df.loc[len(usage_df)] = [access_code, pd.Timestamp(today), 0, 0]
    save_df(usage_df, usage_file)
    mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
idx = usage_df[mask].index[0]

# Gamification
count = usage_df.at[idx, "trial_count"] if trial_mode else usage_df.at[idx, "daily_count"]
if trial_mode and count == 0:
    st.success("🎉 Welcome to your free trial!")
elif not trial_mode and count == 0:
    st.success("🎉 Welcome back!")

# Settings
level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])
if level in ["A1", "A2"]:
    ai_prompt = "Answer using very simple, short sentences and basic words suitable for A1/A2 students."
    grammar_prompt = "Check grammar and give a very short explanation in easy English."
else:
    ai_prompt = f"Answer as a friendly {level} student tutor: use vocabulary and grammar appropriate for {level} learners."
    grammar_prompt = f"Check grammar and provide corrections suitable for a {level} student."

# Conversation Input
user_input = None  # initialize before inputs
uploaded = st.file_uploader("Upload audio (wav/mp3)", type=["wav", "mp3"], key="audio_upload")
if uploaded:
    data = uploaded.read()
    mime = uploaded.type or f"audio/{uploaded.name.split('.')[-1]}"
    st.audio(data, format=mime)
    st.info("🎧 Audio uploaded. To type your next message, clear the audio via the ✖️ on the uploader.")
    # Automatically process transcript when audio is uploaded
    if not st.session_state.get("transcript"):
        try:
            ext = "." + uploaded.name.split(".")[-1]
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            tmp_file.write(data)
            tmp_file.flush()
            resp = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp_file.name, "rb")
            )
            st.session_state["transcript"] = resp.text
        except Exception:
            st.warning("Transcription failed.")
    if st.session_state.get("transcript"):
        user_input = st.session_state["transcript"]
        # clear audio uploader so user can upload next or type
        _ = st.session_state.pop("audio_upload", None)
        # remind student to clear uploaded audio if needed
        st.info("🗒️ Your audio has been processed. Delete the file from the uploader to upload new audio or type your message.")

# Text input
typed = st.chat_input("Or type your message...", key="typed_input")
if not uploaded and typed:
    user_input = typed("Or type your message...", key="typed_input")
if not uploaded and typed:
    user_input = typed

# Display Chat History
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Handle New Input
if user_input:
    usage_col = "trial_count" if trial_mode else "daily_count"
    usage_df.at[idx, usage_col] += 1
    save_df(usage_df, usage_file)
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.chat_message("user")
    st.write(user_input)

    # AI Reply with level tuning
    system_prompt = (
        f"You are Sir Felix, a friendly {language} tutor for {level} students. {ai_prompt}"
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}] + st.session_state["messages"]
    )
    ai_text = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": ai_text})
    st.chat_message("assistant")
    st.write(ai_text)

    # Text-to-Speech
    try:
        lang_map = {"German": "de", "English": "en"}
        tts = gTTS(ai_text, lang=lang_map.get(language, "en"))
        audio_buf = io.BytesIO()
        tts.write_to_fp(audio_buf)
        audio_buf.seek(0)
        st.audio(audio_buf, format="audio/mp3")
    except Exception:
        pass

    # Grammar Correction with level prompt
    gram_system = (
        f"You are a {language} teacher for {level} students. {grammar_prompt} Sentence: {user_input}"
    )
    gram_resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": gram_system}]
    )
    st.info(gram_resp.choices[0].message.content)

# Share Button
share_text = "I just practiced my language skills with Sir Felix!"
st.markdown(f"[Share on WhatsApp](https://wa.me/?text={share_text.replace(' ', '%20')})")
