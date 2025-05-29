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

# --- Custom CSS to hide menu, reactions, and style chat ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .st-emotion, .st-emotion-actions, .st-emotion-cache {visibility: hidden !important;}
    .stChatMessage.user {background: #e1f5fe; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    .stChatMessage.assistant {background: #f0f4c3; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    </style>
""", unsafe_allow_html=True)

st.markdown(
    "<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor!</h2>",
    unsafe_allow_html=True,
)
st.image("https://cdn.pixabay.com/photo/2013/07/13/12/47/student-146981_960_720.png", width=100)
st.markdown("> Practice your speaking or writing. Get simple AI feedback and audio answers!")

# === About Herr Felix & Motivational Exam Bootcamp ===
st.info(
    """
    ### 👋 About Herr Felix

    - 🇬🇭 Born in Ghana, learned German up to C1, and studied in Germany!
    - 🎓 Studied International Management at IU International University.
    - 🏫 Runs Learn Language Education Academy – helping students pass real Goethe exams.
    - 💡 Used to manage a record label and produce music. Now making German learning fun and exam-focused!
    - 🥇 Passionate about your success and making learning entertaining.

    ---
    **🎤 This is not just chat—it's your personal exam preparation bootcamp!**
    - Every time you talk to Herr Felix, imagine you are **in the exam hall**.
    - Expect realistic A2 and B1 speaking questions, surprise prompts, and real exam tips.
    - Sometimes, you’ll even get questions from last year’s exam!

    **Let’s make exam training engaging, surprising, and impactful.**  
    Are you ready? Let’s go! 🚀
    """, icon="💡"
)

# === Expander with A2/B1 Exam Info, Sample Topics, and Downloadable PDFs ===
with st.expander("🎤 German Speaking Exam – A2 & B1: Format, Tips, and Practice Topics (click to expand)"):
    st.markdown("""
    ### 🗣️ **A2 Sprechen (Goethe-Zertifikat) – Structure**
    **Teil 1:** Fragen zu Schlüsselwörtern (Questions based on key words)
    - You and your partner ask and answer questions using cards with keywords.
    - Examples: Wohnort, Beruf, Geburtstag, Hobby, Familie, Reisen, Lieblingsessen, Wetter, etc.

    **Teil 2:** Bildbeschreibung & Diskussion (Picture description & discussion)
    - Speak about a situation using keywords. Example: *Was machen Sie mit Ihrem Geld?* (What do you do with your money?) – Kleidung, Reisen, sparen...

    **Teil 3:** Gemeinsam planen (Planning together)
    - You and your partner plan something together (e.g., Kino, Picknick, Party, Freund besuchen).

    ---
    ### 🗣️ **B1 Sprechen (Goethe-Zertifikat) – Structure**
    **Teil 1:** Planning together (Dialogue): Sommerfest, Reise nach Köln, Museumsbesuch organisieren...
    **Teil 2:** Individual Presentation: Ausbildung, Bio-Essen, Mode, Reisen, Sprachenlernen, Sport, Umweltschutz...
    **Teil 3:** Give feedback and ask questions (e.g., "Ich habe eine Frage: Warum ...?").

    ---
    ### 📄 **Sample A2 Teil 1 Topics**
    Wohnort, Tagesablauf, Freizeit, Sprachen, Essen & Trinken, Haustiere, Lieblingsmonat, Jahreszeit, Sport, Kleidung, Familie, Beruf, Hobbys, Feiertage, Reisen, Lieblingsessen, Schule, Wetter, Auto oder Fahrrad, Perfekter Tag

    ### 📄 **Sample B1 Presentation Topics**
    Ausbildung, Bio-Essen, Chatten, Einkaufen, Facebook, Freiwillige Arbeit, Freundschaft, Haushalt, Haustiere, Heiraten, Leben auf dem Land oder in der Stadt, Mode, Musik, Rauchen, Reisen, Sport treiben, Umweltschutz, Vegetarische Ernährung, etc.

    ---
    **Download full topic sheets for practice:**  
    [A2 Sprechen Topic Sheet (PDF)](sandbox:/mnt/data/A2%20sprechen.pdf)  
    [B1 Sprechen Topic Sheet (PDF)](sandbox:/mnt/data/Sprechen%20B1%20(Goethe%20Exams).pdf)

    *All materials: Learn Language Education Academy*
    """)

# === Entertaining, Impactful Random Exam Topic Trainer ===
import random

a2_topics = [
    "Wohnort", "Tagesablauf", "Freizeit", "Sprachen", "Essen & Trinken", "Haustiere",
    "Lieblingsmonat", "Jahreszeit", "Sport", "Kleidung (Sommer)", "Familie", "Beruf",
    "Hobbys", "Feiertage", "Reisen", "Lieblingsessen", "Schule", "Wetter", "Auto oder Fahrrad", "Perfekter Tag"
]
b1_topics = [
    "Ausbildung", "Berufswahl", "Bio-Essen", "Chatten", "Einkaufen", "Facebook",
    "Freiwillige Arbeit", "Haustiere", "Heiraten", "Leben auf dem Land oder in der Stadt",
    "Mode", "Musikinstrument lernen", "Reisen", "Sport treiben", "Umweltschutz",
    "Vegetarische Ernährung", "Zeitungslesen"
]

st.markdown("---")
st.markdown("## 🎲 **Train Like the Real Exam!**")

exam_level = st.selectbox("Choose exam level for random topic:", ["A2 Sprechen", "B1 Sprechen"], key="exam_level")
if exam_level == "A2 Sprechen":
    if st.button("🎤 Give me a random A2 topic!", key="random_a2"):
        topic = random.choice(a2_topics)
        st.success(f"📝 **Your A2 Sprechen exam topic:**\n\n`{topic}`\n\nImagine you're in the exam! Ask and answer questions about this topic for 1–2 minutes.")
elif exam_level == "B1 Sprechen":
    if st.button("🎤 Give me a random B1 topic!", key="random_b1"):
        topic = random.choice(b1_topics)
        st.success(f"📝 **Your B1 Sprechen exam topic:**\n\n`{topic}`\n\nImagine you're in the exam! Give a short presentation (intro, experience, pros/cons, conclusion).")

st.caption("Keep clicking for more surprise exam-style topics. Every practice session makes you more confident for the real day!")

# === (Your open chat/practice/AI logic continues below as before!) ===


# --- Session State Management ---
if "teacher_rerun" not in st.session_state:
    st.session_state["teacher_rerun"] = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

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

# === COOKIE MANAGER FOR ACCESS CODE ===
cookie_manager = CookiesManager()
access_code = st.text_input(
    "🔐 Enter your paid or trial code:",
    value=cookie_manager.get("falowen_code", ""),
    key="access_code_main"
)
if access_code:
    cookie_manager["falowen_code"] = access_code

mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard"])

# ... your Practice mode and Teacher Dashboard logic continues here ...

# --- Teacher Dashboard ---
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

# ---- Practice Mode ----
language = st.selectbox("🌍 Choose your language", 
    ["German", "French", "English", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic"]
)

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

# --- Access control ---
paid_codes = paid_df["code"].tolist()
access_code = st.text_input("🔐 Enter your paid or trial code:")

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

trial_mode = False
if access_code in paid_codes:
    code_row = paid_df[paid_df["code"] == access_code]
    expiry = code_row["expiry"].values[0]
    if pd.isnull(expiry) or pd.to_datetime(expiry) < datetime.now():
        st.error("Your code has expired. Please subscribe again.")
        st.stop()
elif access_code in trials_df["trial_code"].tolist():
    trial_mode = True
else:
    st.error("Invalid code.")
    st.stop()

# --- Usage tracking ---
today = datetime.now().date()
mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
if not mask.any():
    usage_df.loc[len(usage_df)] = [access_code, pd.Timestamp(today), 0, 0]
    save_usage_df(usage_df)
    mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
row_idx = usage_df[mask].index[0]
trial_count = int(usage_df.at[row_idx, "trial_count"])
daily_count = int(usage_df.at[row_idx, "daily_count"])

# --- Gamification ---
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
        gamification_message = "🎉 Welcome back! Herr Felix is ready to help you learn today."
    elif daily_count in [10, 20]:
        gamification_message = f"🌟 {daily_count} messages sent today! Fantastic dedication."

if gamification_message:
    st.success(gamification_message)

with st.expander("⚙️ Settings", expanded=True):
    level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])

if level in ["A1", "A2"]:
    ai_level_prompt = (
        f"Always answer using very simple, short sentences suitable for {level} students. "
        "Use only basic words. Never use advanced vocabulary. "
        "If the student makes a mistake, gently correct it but do not give long explanations. "
        "For grammar, use easy English only. Respond as simply as possible."
    )
    grammar_level_prompt = (
        "Check this sentence for grammar and spelling mistakes. "
        "Correct the mistake, then give a very short and simple explanation in easy English. "
        "Only use words an A1 or A2 student will understand."
    )
else:
    ai_level_prompt = (
        f"Answer as a {level} language tutor. Use appropriate vocabulary and grammar for {level} level students. "
        "Give clear explanations, but don't make it too complex. Correct mistakes and provide simple grammar notes when needed."
    )
    grammar_level_prompt = (
        f"Check this sentence for grammar and spelling mistakes, and provide corrections and explanations suitable for a {level} student. "
        "Use clear English and, if necessary, explain in the target language."
    )

st.markdown("### 🎤 Upload Your Pronunciation")
st.caption("🎤 Tip: Record at [vocaroo.com](https://www.vocaroo.com) or with your phone's voice recorder (MP3/WAV), then upload below.")

uploaded_audio = st.file_uploader(
    "Upload an audio file (WAV, MP3, OGG, M4A)", type=["wav", "mp3", "ogg", "m4a"], key="audio_upload"
)
if uploaded_audio is not None:
    uploaded_audio.seek(0)
    audio_bytes = uploaded_audio.read()
    st.audio(audio_bytes, format=uploaded_audio.type)
    st.download_button(
        label="⬇️ Download Your Uploaded Audio",
        data=audio_bytes,
        file_name=uploaded_audio.name,
        mime=uploaded_audio.type
    )
    st.info(
        "ℹ️ On iPhone/iPad, audio might not play in the browser. "
        "Please use the 'Download' button to listen in your Files or Music app. "
        "To type, click the ✖️ beside the audio file."
    )
typed_message = st.chat_input("💬 Or type your message here...", key="typed_input")

# --- Handle input ---
user_input = None
if uploaded_audio is not None:
    if not st.session_state.get("transcript"):
        try:
            suffix = "." + uploaded_audio.name.split(".")[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp.name, "rb")
            )
            st.session_state["transcript"] = transcript.text
        except Exception:
            st.warning("Transcription failed. Please try again or type your message.")
            st.session_state["transcript"] = ""
    if st.session_state.get("transcript"):
        user_input = st.session_state["transcript"]
        st.session_state["transcript"] = ""
        if "audio_upload" in st.session_state:
            del st.session_state["audio_upload"]
else:
    st.session_state["transcript"] = ""
    if typed_message:
        user_input = typed_message

# --- Chat display ---
for msg in st.session_state['messages']:
    if msg['role'] == 'assistant':
        with st.chat_message("assistant", avatar="🧑‍🏫"):
            st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Herr Felix:</span> {msg['content']}", unsafe_allow_html=True)
    else:
        with st.chat_message("user"):
            st.markdown(f"🗣️ {msg['content']}")

if user_input:
    if trial_mode:
        usage_df.at[row_idx, "trial_count"] += 1
    else:
        usage_df.at[row_idx, "daily_count"] += 1
    save_usage_df(usage_df)
    st.session_state['messages'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(f"🗣️ {user_input}")

    try:
        ai_system_prompt = (
            f"You are Herr Felix, a friendly {language} tutor. "
            f"{ai_level_prompt}"
        )
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': ai_system_prompt},
                *st.session_state['messages']
            ]
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        ai_reply = "Sorry, there was a problem generating a response. Please try again."
        st.error(str(e))

    st.session_state['messages'].append({'role': 'assistant', 'content': ai_reply})
    with st.chat_message("assistant", avatar="🧑‍🏫"):
        st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Sir Felix:</span> {ai_reply}", unsafe_allow_html=True)
        try:
            lang_codes = {
                "German": "de",
                "French": "fr",
                "Spanish": "es",
                "Italian": "it",
                "Portuguese": "pt",
                "Chinese": "zh-CN",
                "Arabic": "ar",
                "English": "en"
            }
            tts_lang = lang_codes.get(language, "en")
            tts = gTTS(ai_reply, lang=tts_lang)
            tts_bytes = io.BytesIO()
            tts.write_to_fp(tts_bytes)
            tts_bytes.seek(0)
            tts_data = tts_bytes.read()
            st.audio(tts_data, format="audio/mp3")
            st.download_button(
                label="⬇️ Download AI Response Audio",
                data=tts_data,
                file_name="response.mp3",
                mime="audio/mp3"
            )
            st.info(
                "ℹ️ On iPhone/iPad, audio might not play in the browser. "
                "Please use the 'Download' button to listen in your Files or Music app."
            )
        except Exception as e:
            st.info("Audio feedback not available or an error occurred.")
            st.error(str(e))

    # Grammar check
    grammar_prompt = (
        f"You are a {language} teacher helping {level} students. "
        f"{grammar_level_prompt} "
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
    except Exception:
        st.warning("Grammar check failed. Please try again.")

share_text = "I just practiced my language skills with Herr Felix on Falowen! 🌟 Try it too: https://falowen.streamlit.app"
share_url = f"https://wa.me/?text={share_text.replace(' ', '%20')}"
st.markdown(
    f'<a href="{share_url}" target="_blank">'
    '<button style="background:#25D366;color:white;padding:7px 14px;border:none;border-radius:6px;margin-top:10px;font-size:1em;">'
    'Share on WhatsApp 🚀</button></a>',
    unsafe_allow_html=True
)
