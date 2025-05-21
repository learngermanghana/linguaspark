import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta
import pandas as pd
import uuid
import random
import tempfile

# --- Audio recording (optional, handles missing package gracefully) ---
try:
    from streamlit_audiorec import st_audiorec
except ImportError:
    st_audiorec = None

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

# Hide Streamlit logo, hamburger, and footer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .st-emotion-cache-zq5wmm {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "teacher_rerun" not in st.session_state:
    st.session_state["teacher_rerun"] = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- CSV helpers ---
students_file = "students.csv"
trials_file = "trials.csv"
usage_file = "usage.csv"

def save_paid_df(df):
    df["expiry"] = df["expiry"].astype(str)
    df.to_csv(students_file, index=False)

def save_trials_df(df):
    df.to_csv(trials_file, index=False)

def save_usage_df(df):
    df.to_csv(usage_file, index=False)

def load_df(path, cols, date_cols=None):
    try:
        return pd.read_csv(path, parse_dates=date_cols)
    except FileNotFoundError:
        return pd.DataFrame(columns=cols)

paid_df = load_df(students_file, ["code", "expiry"])
if not paid_df.empty:
    paid_df["expiry"] = pd.to_datetime(paid_df["expiry"], errors="coerce")

trials_df = load_df(trials_file, ["email", "trial_code", "created"])
usage_df = load_df(usage_file, ["user_key", "date", "trial_count", "daily_count"], date_cols=["date"])

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# --- Teacher Dashboard (Add, Edit, Delete Codes) ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Manage Paid Codes")
        with st.form("add_paid_code_form"):
            col1, col2 = st.columns([2, 2])
            new_code = col1.text_input("New Paid Code")
            new_expiry = col2.date_input("Expiry Date", value=datetime.now())
            add_btn = col2.form_submit_button("➕ Add Paid Code")
            if add_btn and new_code and new_code not in paid_df["code"].tolist():
                paid_df.loc[len(paid_df)] = [new_code, pd.to_datetime(new_expiry)]
                save_paid_df(paid_df)
                st.success(f"Added paid code {new_code}")
                st.session_state["teacher_rerun"] = True
                st.stop()
        for idx, row in paid_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            col1.text_input(f"Code_{idx}", value=row['code'], key=f"pc_code_{idx}", disabled=True)
            new_expiry = col2.date_input(f"Expiry_{idx}", value=row['expiry'], key=f"pc_exp_{idx}")
            edit_btn = col3.button("💾", key=f"pc_save_{idx}")
            del_btn = col4.button("🗑️", key=f"pc_del_{idx}")
            if edit_btn:
                paid_df.at[idx, "expiry"] = pd.to_datetime(new_expiry)
                save_paid_df(paid_df)
                st.success(f"Updated expiry for {row['code']}")
                st.session_state["teacher_rerun"] = True
                st.stop()
            if del_btn:
                paid_df = paid_df.drop(idx).reset_index(drop=True)
                save_paid_df(paid_df)
                st.success(f"Deleted code {row['code']}")
                st.session_state["teacher_rerun"] = True
                st.stop()
        st.markdown("---")
        st.subheader("🎫 Manage Trial Codes")
        with st.form("add_trial_code_form"):
            col1, col2 = st.columns([3, 2])
            new_email = col1.text_input("New Trial Email")
            add_trial_btn = col2.form_submit_button("Issue Trial Code")
            if add_trial_btn and new_email:
                code_val = uuid.uuid4().hex[:8]
                trials_df.loc[len(trials_df)] = [new_email, code_val, datetime.now()]
                save_trials_df(trials_df)
                st.success(f"Issued trial code {code_val}")
                st.session_state["teacher_rerun"] = True
                st.stop()
        for idx, row in trials_df.iterrows():
            col1, col2, col3, col4 = st.columns([4, 3, 1, 1])
            new_email = col1.text_input(f"TrialEmail_{idx}", value=row['email'], key=f"tc_email_{idx}")
            col2.text_input(f"TrialCode_{idx}", value=row['trial_code'], key=f"tc_code_{idx}", disabled=True)
            edit_btn = col3.button("💾", key=f"tc_save_{idx}")
            del_btn = col4.button("🗑️", key=f"tc_del_{idx}")
            if edit_btn:
                trials_df.at[idx, "email"] = new_email
                save_trials_df(trials_df)
                st.success(f"Updated trial email for {row['trial_code']}")
                st.session_state["teacher_rerun"] = True
                st.stop()
            if del_btn:
                trials_df = trials_df.drop(idx).reset_index(drop=True)
                save_trials_df(trials_df)
                st.success(f"Deleted trial code {row['trial_code']}")
                st.session_state["teacher_rerun"] = True
                st.stop()
    else:
        st.info("Enter correct teacher password.")
    st.stop()

# --- Practice Mode ---
if mode == "Practice":
    # --- Language Selector (add as many as you like) ---
    language = st.selectbox(
        "Language",
        ["German", "French", "English", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic"]
    )

    # ... [tips, facts, challenge, chart, quiz - unchanged] ...

    # --- Audio Pronunciation Practice ---
    st.markdown("### 🎤 Practice Your Pronunciation (optional)")
    if st_audiorec is not None:
        audio_bytes = st_audiorec()
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            st.success("Recording successful! (Sir Felix will review your pronunciation soon.)")
        else:
            st.caption("👆 Press the microphone to record. If it does not work, update your browser, or send your voice note to WhatsApp: 233205706589.")
    else:
        st.warning("Audio recording is not supported in this environment or streamlit_audiorec is not installed.")
        st.caption("You can record a voice note and send it to WhatsApp: 233205706589.")

    # --- Audio Upload Option ---
    st.markdown("#### Or upload an audio file instead of typing:")
    uploaded_audio = st.file_uploader(
        "Upload an audio file (WAV, MP3, OGG, M4A)", type=["wav", "mp3", "ogg", "m4a"]
    )

    user_input = None
    if uploaded_audio is not None:
        st.audio(uploaded_audio)
        # Optional: Transcribe with Whisper if available
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_audio.read())
                tmp.flush()
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp.name, "rb")
            )
            st.success("**Transcription:**")
            st.write(transcript.text)
            # Use transcript as if it were a typed input
            user_input = transcript.text
        except Exception as e:
            st.warning("Transcription failed. Please try again or type your message.")
            user_input = None
    else:
        user_input = st.chat_input("💬 Type your message here...")

    # --- Instructions/Help ---  [unchanged]
    with st.expander("ℹ️ How to Use / Get Access (click to show)"):
        st.markdown("""
        **Trial Access:**  
        - Enter your email below to get a *free trial code* (limited messages).

        **Full Access (Paid):**  
        - If you have a paid code, enter it below for unlimited access.

        **How to get a paid code:**  
        1. Send payment to **233245022743 (Asadu Felix)** via Mobile Money (MTN Ghana).  
        2. After payment, confirm with your tutor or contact WhatsApp: [233205706589](https://wa.me/233205706589)
        """)

    paid_codes = paid_df["code"].tolist()
    access_code = st.text_input("Enter your paid or trial code:")

    if not access_code:
        st.info("Don't have a code? Enter your email to request a free trial code.")
        email_req = st.text_input("Email for trial code")
        if email_req and st.button("Request Trial Code"):
            existing = trials_df[trials_df["email"] == email_req]
            if existing.empty:
                new_code = uuid.uuid4().hex[:8]
                trials_df.loc[len(trials_df)] = [email_req, new_code, datetime.now()]
                save_trials_df(trials_df)
                st.success(f"Your trial code: {new_code}")
            else:
                st.success(f"Your existing trial code: {existing['trial_code'].iloc[0]}")
        st.stop()

    # --- Access Code Validation ---  [unchanged]
    trial_mode = False
    if access_code in paid_codes:
        code_row = paid_df[paid_df["code"] == access_code]
        expiry = code_row["expiry"].values[0]
        if pd.isnull(expiry) or pd.to_datetime(expiry) < datetime.now():
            st.error("Your code has expired. Please subscribe again.")
            st.stop()
        trial_mode = False
    elif access_code in trials_df["trial_code"].tolist():
        trial_mode = True
    else:
        st.error("Invalid code.")
        st.stop()

    # --- Usage tracking ---  [unchanged]
    today = datetime.now().date()
    mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
    if not mask.any():
        usage_df.loc[len(usage_df)] = [access_code, pd.Timestamp(today), 0, 0]
        save_usage_df(usage_df)
        mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
    row_idx = usage_df[mask].index[0]
    trial_count = int(usage_df.at[row_idx, "trial_count"])
    daily_count = int(usage_df.at[row_idx, "daily_count"])

    # --- Usage Limits with Clear Payment Instructions ---  [unchanged]
    if trial_mode and trial_count >= 5:
        st.error("🔒 Your 5-message trial has ended.")
        st.info(
            "To get unlimited access, send payment to 233245022743 (Asadu Felix) and confirm with your tutor for your paid access code. "
            "For help, contact WhatsApp: 233205706589"
        )
        st.stop()

    if not trial_mode and daily_count >= 30:
        st.warning("🚫 Daily limit reached for today.")
        st.info(
            "To increase your daily limit or renew your access, send payment to 233245022743 (Asadu Felix) and confirm with your tutor for your paid access code. "
            "For help, contact WhatsApp: 233205706589"
        )
        st.stop()

    # --- Gamification Celebrations ---  [unchanged]
    gamification_message = ""
    if trial_mode:
        if trial_count == 0:
            gamification_message = "🎉 Welcome! Start chatting to practice your language skills with Sir Felix."
        elif trial_count == 1:
            gamification_message = "🌟 You sent your first message. Keep going!"
        elif trial_count == 3:
            gamification_message = "🔥 You’ve sent 3 messages! You're making great progress."
        elif trial_count == 4:
            gamification_message = "🚀 One more message left in your free trial. Upgrade for unlimited practice!"
    else:
        if daily_count == 0:
            gamification_message = "🎉 Welcome back! Sir Felix is ready to help you learn today."
        elif daily_count in [10, 20]:
            gamification_message = f"🌟 {daily_count} messages sent today! Fantastic dedication."

    if gamification_message:
        st.success(gamification_message)

    def increment_usage(is_trial: bool):
        if is_trial:
            usage_df.at[row_idx, "trial_count"] += 1
        else:
            usage_df.at[row_idx, "daily_count"] += 1
        save_usage_df(usage_df)

    # --- Settings ---  [unchanged]
    with st.expander("⚙️ Settings", expanded=True):
        level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])

    # Determine display name
    if trial_mode:
        row = trials_df[trials_df["trial_code"] == access_code]
        display = row["email"].values[0].split("@")[0].replace('.', ' ').title() if not row.empty else "Learner"
    else:
        display = "Student"

    # --- Chat Interface with Mascot ---
    for msg in st.session_state['messages']:
        if msg['role'] == 'assistant':
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"**Sir Felix:** {msg['content']}")
        else:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])

    # --- User Message Submission Logic ---
    if user_input:
        increment_usage(trial_mode)
        st.session_state['messages'].append({'role': 'user', 'content': user_input})
        st.chat_message('user').markdown(user_input)

        try:
            # AI conversation response
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': f"You are Sir Felix, a friendly {language} tutor. Always encourage and explain simply."},
                    *st.session_state['messages']
                ]
            )
            ai_reply = response.choices[0].message.content
        except Exception as e:
            ai_reply = "Sorry, there was a problem generating a response. Please try again."
            st.error(str(e))

        st.session_state['messages'].append({'role': 'assistant', 'content': ai_reply})
        with st.chat_message("assistant", avatar="🧑‍🏫"):
            st.markdown(f"**Sir Felix:** {ai_reply}")

        # --- GRAMMAR CHECK ---
        if language in ["German", "French", "English", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic"]:
            grammar_prompt = (
                f"You are Sir Felix, a helpful {language} teacher. "
                f"Check the following sentence for grammar, spelling, and phrasing errors. "
                f"Give the corrected sentence and a short explanation. "
                f"Sentence: {user_input}"
            )
            try:
                grammar_response = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{"role": "system", "content": grammar_prompt}],
                    max_tokens=120
                )
                grammar_reply = grammar_response.choices[0].message.content.strip()
                st.info(f"📝 **Sir Felix's Correction:**\n{grammar_reply}")
            except Exception as e:
                st.warning("Grammar check failed. Please try again.")

    # --- Social Sharing Button (after chat) ---
    share_text = "I just practiced my language skills with Sir Felix on Falowen! 🌟 Try it too: https://falowen.streamlit.app"
    share_url = f"https://wa.me/?text={share_text.replace(' ', '%20')}"
    st.markdown(
        f'<a href="{share_url}" target="_blank">'
        '<button style="background:#25D366;color:white;padding:7px 14px;border:none;border-radius:6px;margin-top:10px;font-size:1em;">'
        'Share on WhatsApp 🚀</button></a>',
        unsafe_allow_html=True
    )
