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

# --- Custom CSS to hide default menu and style chat ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stChatMessage.user {background: #e1f5fe; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    .stChatMessage.assistant {background: #f0f4c3; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## 🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor!")
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

# --- Data load/save helpers ---
def save_df(df, path):
    df.to_csv(path, index=False)

def load_df(path, cols, date_cols=None):
    try:
        return pd.read_csv(path, parse_dates=date_cols)
    except FileNotFoundError:
        return pd.DataFrame(columns=cols)

# Load paid and trial codes, usage
paid_df = load_df(students_file, ["code", "expiry"], date_cols=["expiry"])
paid_df["expiry"] = pd.to_datetime(paid_df["expiry"], errors="coerce")
trials_df = load_df(trials_file, ["email", "trial_code", "created"], date_cols=["created"])
usage_df = load_df(usage_file, ["user_key", "date", "trial_count", "daily_count"], date_cols=["date"])

# --- Sidebar navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Manage Paid Codes")
        with st.form("add_paid"):  # Add new paid code
            c1, c2 = st.columns([2,2])
            new_code = c1.text_input("New Paid Code")
            new_expiry = c2.date_input("Expiry Date", datetime.now())
            if st.form_submit_button("Add Paid Code"):
                paid_df.loc[len(paid_df)] = [new_code, pd.to_datetime(new_expiry)]
                save_df(paid_df, students_file)
                st.success(f"Added paid code: {new_code}")
        st.markdown("---")
        st.subheader("🎫 Manage Trial Codes")
        with st.form("add_trial"):  # Issue new trial code
            email = st.text_input("Email for Trial Code")
            if st.form_submit_button("Issue Trial Code"):
                code_val = uuid.uuid4().hex[:8]
                trials_df.loc[len(trials_df)] = [email, code_val, datetime.now()]
                save_df(trials_df, trials_file)
                st.success(f"Issued trial code: {code_val}")
    else:
        st.info("Enter correct teacher password.")
    st.stop()

# --- Practice Mode ---
language = st.selectbox("🌍 Choose your language", [
    "German","French","English","Spanish","Italian","Portuguese","Chinese","Arabic"
])
with st.expander("ℹ️ How to Use / Get Access"):
    st.markdown(
        """
**Trial Access:** Enter email for free trial code.

**Paid Access:** Enter your paid code. Contact tutor on WhatsApp after payment.
        """
    )

# Access control
access_code = st.text_input("🔐 Enter paid/trial code:")
if not access_code:
    st.info("Enter code or email above to proceed.")
    st.stop()

trial_mode = False
if access_code in paid_df["code"].tolist():
    exp = paid_df.loc[paid_df["code"] == access_code, "expiry"].iloc[0]
    if pd.isna(exp) or exp < datetime.now():
        st.error("Paid code expired.")
        st.stop()
elif access_code in trials_df["trial_code"].tolist():
    trial_mode = True
else:
    st.error("Invalid code.")
    st.stop()

# Usage tracking
today = datetime.now().date()
row = usage_df[(usage_df.user_key==access_code) & (usage_df.date==pd.Timestamp(today))]
if row.empty:
    usage_df.loc[len(usage_df)] = [access_code, pd.Timestamp(today), 0, 0]
    save_df(usage_df, usage_file)
    row = usage_df[(usage_df.user_key==access_code) & (usage_df.date==pd.Timestamp(today))]
idx = row.index[0]

# Gamification
count = usage_df.at[idx, "trial_count"] if trial_mode else usage_df.at[idx, "daily_count"]
if count==0:
    st.success("🎉 Welcome!")

# Settings
level = st.selectbox("Level", ["A1","A2","B1","B2","C1"])
# Define prompts
ai_prompt = (
    "Use simple language." if level in ["A1","A2"] else "Use appropriate {level} level."
)
grammar_prompt = ai_prompt

# Conversation UI
uploaded = st.file_uploader("Upload audio (wav/mp3)", type=["wav","mp3"], key="audio_upload")
text = st.chat_input("Or type your message...")

user_input = None
if uploaded:
    st.audio(uploaded)
    if not st.session_state["transcript"]:
        try:
            ext = "." + uploaded.name.split('.')[-1]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            tmp.write(uploaded.read()); tmp.flush()
            res = client.audio.transcriptions.create(model="whisper-1", file=open(tmp.name,'rb'))
            st.session_state["transcript"] = res.text
        except:
            st.warning("Transcription failed.")
    if st.session_state["transcript"]:
        st.write(st.session_state["transcript"])
        if st.button("Submit Audio"):
            user_input = st.session_state["transcript"]
            st.session_state["transcript"] = ""
            _ = st.session_state.pop("audio_upload", None)
            st.stop()
elif text:
    user_input = text

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg['role']):
        st.write(msg['content'])

# Handle new user input
if user_input:
    usage_col = "trial_count" if trial_mode else "daily_count"
    usage_df.at[idx, usage_col] += 1
    save_df(usage_df, usage_file)
    st.session_state["messages"].append({'role':'user','content':user_input})
    st.chat_message("user")
    st.write(user_input)

    # AI response
    sys = f"You are a {language} tutor. {ai_prompt}"
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{'role':'system','content':sys}, *st.session_state["messages"]]
    )
    reply = res.choices[0].message.content
    st.session_state["messages"].append({'role':'assistant','content':reply})
    st.chat_message("assistant")
    st.write(reply)

    # TTS
    try:
        code_map={"German":"de","English":"en"}
        tts= gTTS(reply, lang=code_map.get(language,'en'))
        buf=io.BytesIO(); tts.write_to_fp(buf); buf.seek(0)
        st.audio(buf)
    except:
        pass

    # Grammar correction
    gram_sys = f"Check grammar: {grammar_prompt} Sentence: {user_input}"
    gres = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{'role':'system','content':gram_sys}]
    )
    greply = gres.choices[0].message.content
    st.info(greply)

# Share button
share = "I practiced with Sir Felix!"
st.markdown(f"[Share on WhatsApp](https://wa.me/?text={share})")
