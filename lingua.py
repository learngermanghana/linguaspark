import streamlit as st
from openai import OpenAI
import tempfile
import io
from gtts import gTTS
import random
import re
import pandas as pd
import os
from datetime import date

st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ======= CODE MANAGEMENT FUNCTIONS =======
CODES_FILE = "student_codes.csv"
TEACHER_PASSWORD = "Felix029"

def load_codes():
    if os.path.exists(CODES_FILE):
        df = pd.read_csv(CODES_FILE)
        if "code" not in df.columns:
            df = pd.DataFrame(columns=["code"])
        df["code"] = df["code"].astype(str).str.strip().str.lower()
    else:
        df = pd.DataFrame(columns=["code"])
    return df

# Step control
if "step" not in st.session_state:
    st.session_state["step"] = 1

if "student_code" not in st.session_state:
    st.session_state["student_code"] = ""

if "selected_mode" not in st.session_state:
    st.session_state["selected_mode"] = "Geführte Prüfungssimulation (Exam Mode)"

if "custom_topic" not in st.session_state:
    st.session_state["custom_topic"] = ""

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "corrections" not in st.session_state:
    st.session_state["corrections"] = []
if "turn_count" not in st.session_state:
    st.session_state["turn_count"] = 0

if "daily_usage" not in st.session_state:
    st.session_state["daily_usage"] = {}

today_str = str(date.today())
usage_key = f"{st.session_state['student_code']}_{today_str}"
if usage_key not in st.session_state["daily_usage"]:
    st.session_state["daily_usage"][usage_key] = 0

DAILY_LIMIT = 25
max_turns = 6

# ========== STEP 1: STUDENT CODE ==========
if st.session_state["step"] == 1:
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️"):
        code_clean = code.strip().lower()
        df_codes = load_codes()
        if code_clean in df_codes["code"].dropna().tolist():
            st.session_state["student_code"] = code_clean
            st.session_state["step"] = 2
        else:
            st.error("This code is not recognized. Please check with your tutor.")

# ========== STEP 2: WELCOME SCREEN ==========
elif st.session_state["step"] == 2:
    st.markdown("<h2 style='font-weight:bold'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor, Herr Felix!</h2>", unsafe_allow_html=True)
    st.markdown("> Practice your German speaking or writing. Get simple AI feedback and audio answers!")
    st.info(
        """
        🎤 **This is not just chat—it's your personal exam preparation bootcamp!**

        Every time you talk to Herr Felix, imagine you are **in the exam hall**.
        Expect realistic A2 and B1 speaking questions, surprise prompts, and real exam tips—sometimes, you’ll even get questions from last year’s exam!

        **Want to prepare for a class presentation or your next homework?**
        👉 You can also enter your **own question or topic** at any time—perfect for practicing real classroom situations or special assignments!

        Let’s make exam training engaging, surprising, and impactful.  
        **Are you ready? Let’s go! 🚀**
        """, icon="💡"
    )
    if st.button("Next ➡️"):
        st.session_state["step"] = 3
    if st.button("⬅️ Back"):
        st.session_state["step"] = 1

# ========== STEP 3: PRACTICE MODE ==========
elif st.session_state["step"] == 3:
    st.header("Wie möchtest du üben?")
    mode = st.radio(
        "What would you like to practice?",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)"],
        index=0,
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode

    custom_topic = ""
    if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
        custom_topic = st.text_input("Type your own topic or question here (e.g. from Google Classroom, homework, or any free conversation)...", value=st.session_state.get("custom_topic", ""))
        st.session_state["custom_topic"] = custom_topic
    if st.button("Start Practice ➡️"):
        st.session_state["step"] = 4
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["corrections"] = []
    if st.button("⬅️ Back"):
        st.session_state["step"] = 2

# ========== STEP 4: MAIN CHAT ==========
elif st.session_state["step"] == 4:
    # Quick helpers for main mode
    mode = st.session_state["selected_mode"]
    custom_topic = st.session_state.get("custom_topic", "")
    exam_level = st.session_state.get("exam_level", "A2")
    if mode == "Geführte Prüfungssimulation (Exam Mode)":
        if "exam_level" not in st.session_state:
            st.session_state["exam_level"] = "A2"
        exam_level = st.selectbox("Welches Prüfungsniveau möchtest du üben?", ["A2", "B1"], key="exam_level")
        st.session_state["exam_level"] = exam_level

    st.info(f"Student code: `{st.session_state['student_code']}` | Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}")

    # --- Pick topic (for exam mode) ---
    if not st.session_state["messages"]:
        if mode == "Geführte Prüfungssimulation (Exam Mode)":
            if exam_level == "A2":
                topics = [
                    "Wohnort", "Tagesablauf", "Freizeit", "Sprachen", "Essen & Trinken", "Haustiere",
                    "Lieblingsmonat", "Jahreszeit", "Sport", "Kleidung (Sommer)", "Familie", "Beruf",
                    "Hobbys", "Feiertage", "Reisen", "Lieblingsessen", "Schule", "Wetter", "Auto oder Fahrrad", "Perfekter Tag"
                ]
                topic = random.choice(topics)
                prompt = f"**A2 Teil 1:** Das Schlüsselwort ist **{topic}**. Stelle eine passende Frage und beantworte eine Frage dazu. Beispiel: 'Hast du Geschwister? – Ja, ich habe eine Schwester.'"
            else:
                topics = [
                    "Mithilfe beim Sommerfest", "Eine Reise nach Köln planen", "Überraschungsparty organisieren",
                    "Kulturelles Ereignis (Konzert, Ausstellung) planen", "Museumsbesuch organisieren"
                ]
                topic = random.choice(topics)
                prompt = f"**B1 Teil 1:** Plant gemeinsam: **{topic}**. Mache Vorschläge, reagiere auf deinen Partner, und trefft eine Entscheidung."
            st.session_state["messages"].append({"role": "assistant", "content": prompt})
        elif mode == "Eigenes Thema/Frage (Custom Topic Chat)" and custom_topic.strip():
            st.session_state["messages"].append({"role": "user", "content": custom_topic.strip()})

    # === Chat Input ===
    uploaded_audio = st.file_uploader("Upload an audio file (WAV, MP3, OGG, M4A)", type=["wav", "mp3", "ogg", "m4a"], key="audio_upload")
    typed_message = st.chat_input("💬 Oder tippe deine Antwort hier...", key="typed_input")

    # === Chat Logic ===
    user_input = None
    if uploaded_audio is not None:
        uploaded_audio.seek(0)
        audio_bytes = uploaded_audio.read()
        st.audio(audio_bytes, format=uploaded_audio.type)
        try:
            suffix = "." + uploaded_audio.name.split(".")[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
            client = OpenAI(api_key=st.secrets.get("general", {}).get("OPENAI_API_KEY"))
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp.name, "rb")
            )
            user_input = transcript.text
        except Exception:
            st.warning("Transcription failed. Please try again or type your message.")
    elif typed_message:
        user_input = typed_message

    session_ended = st.session_state["turn_count"] >= max_turns
    used_today = st.session_state["daily_usage"][usage_key]

    # 1. --- Append and display the student message instantly ---
    if user_input and not session_ended:
        if used_today >= DAILY_LIMIT:
            st.warning("You’ve reached today’s free practice limit. Please come back tomorrow or contact your tutor for unlimited access!")
        else:
            st.session_state['messages'].append({'role': 'user', 'content': user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1

    # 2. --- Display all chat history, always up to date ---
    for msg in st.session_state['messages']:
        if msg['role'] == 'assistant':
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Herr Felix:</span> {msg['content']}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # 3. --- Generate and append AI reply (with correction), always visible as text ---
    if user_input and not session_ended and used_today < DAILY_LIMIT:
        try:
            extra_end = (
                "After 6 student answers, give a short, positive summary, "
                "suggest a new topic or a break, and do NOT answer further unless restarted."
                if st.session_state["turn_count"] >= max_turns else ""
            )
            if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                ai_system_prompt = (
                    "You are Herr Felix, an expert German teacher and exam trainer. "
                    "Only correct and give a grammar tip for the student's most recent answer, never your own messages. "
                    "First, answer the student's question or statement naturally as a German tutor (max 2–3 sentences). "
                    "Then, if there are mistakes, show the corrected sentence(s) clearly under 'Correction:'. "
                    "After that, give a very short 'Grammatik-Tipp:' explaining the main issue. "
                    "If the student's answer is perfect, say so and still give a tip. "
                    "Finally, always end your message with a follow-up question or prompt to keep the conversation going. "
                    + extra_end +
                    " Never break character."
                )
            else:
                if exam_level == "A2":
                    ai_system_prompt = (
                        "You are Herr Felix, a strict but friendly Goethe A2 examiner. "
                        "Only correct and give a grammar tip for the student's most recent answer, never your own messages. "
                        "First, answer the student's question or statement in very simple A2-level German (max 2–3 sentences). "
                        "Then, if there are mistakes, show the corrected sentence(s) clearly under 'Correction:'. "
                        "After that, give a very short 'Grammatik-Tipp:' with a brief, simple explanation. "
                        "If the answer is perfect, say so and still give a tip. "
                        "Finally, always end your message with a follow-up question or prompt to keep the conversation going. "
                        "Never use advanced vocabulary. "
                        + extra_end +
                        " Never break character."
                    )
                else:
                    ai_system_prompt = (
                        "You are Herr Felix, a strict but supportive Goethe B1 examiner. "
                        "Only correct and give a grammar tip for the student's most recent answer, never your own messages. "
                        "First, answer the student's question or statement in B1-level German (max 2–3 sentences). "
                        "Then, if there are mistakes, show the corrected sentence(s) clearly under 'Correction:'. "
                        "After that, give a very short 'Grammatik-Tipp:' with a brief explanation. "
                        "If the answer is perfect, say so and still give a tip. "
                        "Finally, always end your message with a follow-up question or prompt to keep the conversation going. "
                        + extra_end +
                        " Never break character."
                    )

            client = OpenAI(api_key=st.secrets.get("general", {}).get("OPENAI_API_KEY"))
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

        # Play AI audio for every AI reply, but always show the text too
        try:
            tts = gTTS(ai_reply, lang="de")
            tts_bytes = io.BytesIO()
            tts.write_to_fp(tts_bytes)
            tts_bytes.seek(0)
            tts_data = tts_bytes.read()
            st.audio(tts_data, format="audio/mp3")
        except Exception:
            st.info("Audio feedback not available or an error occurred.")

    if session_ended:
        st.success("🎉 **Session beendet!** Du hast fleißig geübt. Willst du ein neues Thema oder eine Pause?")
        if st.button("Neue Session starten"):
            st.session_state["messages"] = []
            st.session_state["corrections"] = []
            st.session_state["turn_count"] = 0

    if st.button("⬅️ Back to mode selection"):
        st.session_state["step"] = 3
        st.session_state["messages"] = []
        st.session_state["corrections"] = []
        st.session_state["turn_count"] = 0
