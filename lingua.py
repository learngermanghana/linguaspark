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

CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
max_turns = 6
TEACHER_PASSWORD = "Felix029"

# ==== Topic lists ====
A2_TEIL1 = [
    "Wohnort", "Tagesablauf", "Freizeit", "Sprachen", "Essen & Trinken", "Haustiere",
    "Lieblingsmonat", "Jahreszeit", "Sport", "Kleidung (Sommer)", "Familie", "Beruf",
    "Hobbys", "Feiertage", "Reisen", "Lieblingsessen", "Schule", "Wetter", "Auto oder Fahrrad", "Perfekter Tag"
]
A2_TEIL2 = [
    "Was machen Sie mit Ihrem Geld?",
    "Was machen Sie am Wochenende?",
    "Wie verbringen Sie Ihren Urlaub?",
    "Wie oft gehen Sie einkaufen und was kaufen Sie?",
    "Was für Musik hören Sie gern?",
    "Wie feiern Sie Ihren Geburtstag?",
    "Welche Verkehrsmittel nutzen Sie?",
    "Wie bleiben Sie gesund?",
    "Was machen Sie gern mit Ihrer Familie?",
    "Wie sieht Ihr Traumhaus aus?",
    "Welche Filme oder Serien mögen Sie?",
    "Wie oft gehen Sie ins Restaurant?",
    "Was ist Ihr Lieblingsfeiertag?",
    "Was machen Sie morgens als Erstes?",
    "Wie lange schlafen Sie normalerweise?",
    "Welche Hobbys hatten Sie als Kind?",
    "Machen Sie lieber Urlaub am Meer oder in den Bergen?",
    "Wie sieht Ihr Lieblingszimmer aus?",
    "Was ist Ihr Lieblingsgeschäft?",
    "Wie sieht ein perfekter Tag für Sie aus?"
]
A2_TEIL3 = [
    "Zusammen ins Kino gehen", "Ein Café besuchen", "Gemeinsam einkaufen gehen",
    "Ein Picknick im Park organisieren", "Eine Fahrradtour planen",
    "Zusammen in die Stadt gehen", "Einen Ausflug ins Schwimmbad machen",
    "Eine Party organisieren", "Zusammen Abendessen gehen",
    "Gemeinsam einen Freund/eine Freundin besuchen", "Zusammen ins Museum gehen",
    "Einen Spaziergang im Park machen", "Ein Konzert besuchen",
    "Zusammen eine Ausstellung besuchen", "Einen Wochenendausflug planen",
    "Ein Theaterstück ansehen", "Ein neues Restaurant ausprobieren",
    "Einen Kochabend organisieren", "Einen Sportevent besuchen", "Eine Wanderung machen"
]

B1_TEIL1 = [
    "Mithilfe beim Sommerfest", "Eine Reise nach Köln planen",
    "Überraschungsparty organisieren", "Kulturelles Ereignis (Konzert, Ausstellung) planen",
    "Museumsbesuch organisieren"
]
B1_TEIL2 = [
    "Ausbildung", "Auslandsaufenthalt", "Behinderten-Sport", "Berufstätige Eltern",
    "Berufswahl", "Bio-Essen", "Chatten", "Computer für jeden Kursraum", "Das Internet",
    "Einkaufen in Einkaufszentren", "Einkaufen im Internet", "Extremsport", "Facebook",
    "Fertigessen", "Freiwillige Arbeit", "Freundschaft", "Gebrauchte Kleidung",
    "Getrennter Unterricht für Jungen und Mädchen", "Haushalt", "Haustiere", "Heiraten",
    "Hotel Mama", "Ich bin reich genug", "Informationen im Internet", "Kinder und Fernsehen",
    "Kinder und Handys", "Kinos sterben", "Kreditkarten", "Leben auf dem Land oder in der Stadt",
    "Makeup für Kinder", "Marken-Kleidung", "Mode", "Musikinstrument lernen",
    "Musik im Zeitalter des Internets", "Rauchen", "Reisen", "Schokolade macht glücklich",
    "Sport treiben", "Sprachenlernen", "Sprachenlernen mit dem Internet",
    "Stadtzentrum ohne Autos", "Studenten und Arbeit in den Ferien", "Studium", "Tattoos",
    "Teilzeitarbeit", "Unsere Idole", "Umweltschutz", "Vegetarische Ernährung", "Zeitungslesen"
]
B1_TEIL3 = [
    "Fragen stellen zu einer Präsentation", "Positives Feedback geben",
    "Etwas überraschend finden oder planen", "Weitere Details erfragen"
]

def load_codes():
    if os.path.exists(CODES_FILE):
        df = pd.read_csv(CODES_FILE)
        if "code" not in df.columns:
            df = pd.DataFrame(columns=["code"])
        df["code"] = df["code"].astype(str).str.strip().str.lower()
    else:
        df = pd.DataFrame(columns=["code"])
    return df

# ========== TEACHER DASHBOARD (SIDEBAR) ==========
with st.sidebar:
    if "teacher_authenticated" not in st.session_state:
        st.session_state["teacher_authenticated"] = False

    # --- Teacher login prompt if not authenticated ---
    if not st.session_state["teacher_authenticated"]:
        st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)  # Blank space
        # Optionally, uncomment below to show a logo
        # st.image("your_logo.png", width=120)
        pwd = st.text_input("Teacher Login (for admin only)", type="password")
        login_btn = st.button("Login (Teacher)")
        if login_btn:
            if pwd == TEACHER_PASSWORD:
                st.session_state["teacher_authenticated"] = True
                st.success("Access granted!")
            elif pwd != "":
                st.error("Incorrect password. Please try again.")

    # --- Teacher dashboard (settings) ---
    else:
        st.header("👩‍🏫 Teacher Dashboard")
        df_codes = load_codes()
        st.subheader("Current Codes")
        st.dataframe(df_codes, use_container_width=True)

        new_code = st.text_input("Add a new student code")
        if st.button("Add Code"):
            new_code_clean = new_code.strip().lower()
            if new_code_clean and new_code_clean not in df_codes["code"].values:
                df_codes = pd.concat([df_codes, pd.DataFrame({"code": [new_code_clean]})], ignore_index=True)
                df_codes.to_csv(CODES_FILE, index=False)
                st.success(f"Code '{new_code_clean}' added!")
            elif not new_code_clean:
                st.warning("Enter a code to add.")
            else:
                st.warning("Code already exists.")

        remove_code = st.selectbox("Select code to remove", [""] + df_codes["code"].tolist())
        if st.button("Remove Selected Code"):
            if remove_code:
                df_codes = df_codes[df_codes["code"] != remove_code]
                df_codes.to_csv(CODES_FILE, index=False)
                st.success(f"Code '{remove_code}' removed!")
            else:
                st.warning("Choose a code to remove.")

        if st.button("Log out (Teacher)"):
            st.session_state["teacher_authenticated"] = False


# ====== STEPPER STAGES ======
if "step" not in st.session_state:
    st.session_state["step"] = 1
if "student_code" not in st.session_state:
    st.session_state["student_code"] = ""
if "daily_usage" not in st.session_state:
    st.session_state["daily_usage"] = {}
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "corrections" not in st.session_state:
    st.session_state["corrections"] = []
if "turn_count" not in st.session_state:
    st.session_state["turn_count"] = 0

# ------ Stage 1: Student Login ------
if st.session_state["step"] == 1:
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️", key="stage1_next"):
        code_clean = code.strip().lower()
        df_codes = load_codes()
        if code_clean in df_codes["code"].dropna().tolist():
            st.session_state["student_code"] = code_clean
            st.session_state["step"] = 2
        else:
            st.error("This code is not recognized. Please check with your tutor.")

# ------ Stage 2: Welcome ------
elif st.session_state["step"] == 2:
    fun_facts = [
        "🇬🇭 Herr Felix was born in Ghana and mastered German up to C1 level!",
        "🎓 Herr Felix studied International Management at IU International University in Germany.",
        "🏫 He founded Learn Language Education Academy to help students pass Goethe exams.",
        "💡 Herr Felix used to run a record label and produce music before becoming a language coach!",
        "🥇 He loves making language learning fun, personal, and exam-focused.",
        "📚 Herr Felix speaks English, German, and loves teaching in both.",
        "🚀 Sometimes Herr Felix will throw in a real Goethe exam question—are you ready?",
        "🤖 Herr Felix built this app himself—so every session is personalized!"
    ]
    st.success(f"**Did you know?** {random.choice(fun_facts)}")
    st.markdown(
        "<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor, Herr Felix!</h2>",
        unsafe_allow_html=True,
    )
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
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage2_back"):
            st.session_state["step"] = 1
    with col2:
        if st.button("Next ➡️", key="stage2_next"):
            st.session_state["step"] = 3

# ------ Stage 3: Mode Selection ------
elif st.session_state["step"] == 3:
    st.header("Wie möchtest du üben? (How would you like to practice?)")
    mode = st.radio(
        "Choose your practice mode:",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)"],
        index=0,
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode
    custom_topic = ""
    if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
        custom_topic = st.text_input("Type your own topic or question here...", value=st.session_state.get("custom_topic", ""), key="custom_topic_input")
        st.session_state["custom_topic"] = custom_topic
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage3_back"):
            st.session_state["step"] = 2
    with col2:
        if st.button("Next ➡️", key="stage3_next"):
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                st.session_state["step"] = 5
            else:
                st.session_state["step"] = 4
# ------ Stage 4: Exam Part Selection ------
elif st.session_state["step"] == 4:
    st.header("Prüfungsteil wählen / Choose exam part")
    exam_level = st.selectbox(
        "Welches Prüfungsniveau möchtest du üben?",
        ["A2", "B1"],
        key="exam_level_select",
        index=0
    )
    st.session_state["selected_exam_level"] = exam_level

    teil_options = (
        [
            "Teil 1 – Fragen zu Schlüsselwörtern",
            "Teil 2 – Bildbeschreibung & Diskussion",
            "Teil 3 – Gemeinsam planen"
        ] if exam_level == "A2" else
        [
            "Teil 1 – Gemeinsam planen (Dialogue)",
            "Teil 2 – Präsentation (Monologue)",
            "Teil 3 – Feedback & Fragen stellen"
        ]
    )
    teil = st.selectbox(
        "Welchen Teil möchtest du üben?",
        teil_options,
        key="exam_teil_select"
    )
    st.session_state["selected_teil"] = teil

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage4_back"):
            st.session_state["step"] = 3
    with col2:
        if st.button("Start Chat ➡️", key="stage4_start"):
            if exam_level == "A2":
                if teil.startswith("Teil 1"):
                    topic = random.choice(A2_TEIL1)
                    prompt = f"**A2 Teil 1:** Das Schlüsselwort ist **{topic}**. Stelle eine passende Frage und beantworte eine Frage dazu. Beispiel: 'Hast du Geschwister? – Ja, ich habe eine Schwester.'"
                elif teil.startswith("Teil 2"):
                    topic = random.choice(A2_TEIL2)
                    prompt = f"**A2 Teil 2:** Beschreibe oder diskutiere zum Thema: **{topic}**."
                else:
                    topic = random.choice(A2_TEIL3)
                    prompt = f"**A2 Teil 3:** Plant gemeinsam: **{topic}**. Mache Vorschläge, reagiere, und trefft eine Entscheidung."
            else:
                if teil.startswith("Teil 1"):
                    topic = random.choice(B1_TEIL1)
                    prompt = f"**B1 Teil 1:** Plant gemeinsam: **{topic}**. Mache Vorschläge, reagiere auf deinen Partner, und trefft eine Entscheidung."
                elif teil.startswith("Teil 2"):
                    topic = random.choice(B1_TEIL2)
                    prompt = f"**B1 Teil 2:** Halte eine Präsentation über das Thema: **{topic}**. Begrüße, nenne das Thema, gib deine Meinung, teile Vor- und Nachteile, fasse zusammen."
                else:
                    topic = random.choice(B1_TEIL3)
                    prompt = f"**B1 Teil 3:** {topic}: Dein Partner hat eine Präsentation gehalten. Stelle 1–2 Fragen dazu und gib positives Feedback."
            st.session_state["initial_prompt"] = prompt
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["step"] = 5

# ------ Stage 5: Chat & Correction ------
if st.session_state["step"] == 5:
    # --- Setup daily_usage
    if "daily_usage" not in st.session_state:
        st.session_state["daily_usage"] = {}
    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    if usage_key not in st.session_state["daily_usage"]:
        st.session_state["daily_usage"][usage_key] = 0

    st.info(
        f"Student code: `{student_code}` | "
        f"Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}"
    )

    # --- B1 Teil 3: Special "role-play" prompt ---
    is_b1_teil3 = (
        st.session_state.get("selected_mode", "").startswith("Geführte") and
        st.session_state.get("selected_exam_level", "") == "B1" and
        st.session_state.get("selected_teil", "").startswith("Teil 3")
    )

    # Insert first message for B1 Teil 3
    if is_b1_teil3 and not st.session_state["messages"]:
        topic = random.choice(B1_TEIL2)
        st.session_state["current_b1_teil3_topic"] = topic
        initial_prompt = (
            f"Ich habe gerade eine kurze Präsentation über **{topic}** gehalten.\n\n"
            "Deine Aufgabe jetzt:\n"
            "- Stelle mir **zwei Fragen** zu meiner Präsentation (auf Deutsch).\n"
            "- Gib mir **eine positive Rückmeldung** auf Deutsch.\n\n"
            "👉 Schreib deine zwei Fragen und ein Feedback jetzt unten auf!"
        )
        st.session_state["messages"].append({"role": "assistant", "content": initial_prompt})

    # Insert first message for all other modes
    elif not st.session_state["messages"]:
        if st.session_state.get("selected_mode", "").startswith("Geführte"):
            prompt = st.session_state.get("initial_prompt", "Stelle bitte eine Frage oder beginne mit deiner Präsentation.")
            st.session_state["messages"].append({"role": "assistant", "content": prompt})
        else:
            custom_topic = st.session_state.get("custom_topic", "")
            if custom_topic:
                st.session_state["messages"].append({"role": "user", "content": custom_topic})
                # For custom topic, AI begins the conversation as before
                try:
                    ai_system_prompt = (
                        "You are Herr Felix, an expert German teacher and presentation coach. "
                        "The student has just given you a topic or question for practice (e.g. class presentation, homework, or exam training). "
                        "Start the conversation right away: reply directly to the student's topic, ask a relevant follow-up question, and give an example answer if it fits. "
                        "Be engaging and supportive, like a real exam partner or teacher, and always give a 'Grammatik-Tipp:' in English using simple language, or a brief correction if needed. "
                        "Keep your responses short (max. 2–3 sentences). "
                        "If the student's message is already a good presentation, praise it and help them go deeper or extend the topic. "
                        "Never say 'How can I help you?'. Instead, react directly to the topic and keep the conversation going. "
                        "Never break character."
                    )
                    client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                    response = client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[{"role": "system", "content": ai_system_prompt}, *st.session_state["messages"]],
                    )
                    ai_reply = response.choices[0].message.content
                except Exception as e:
                    ai_reply = "Sorry, there was a problem generating a response. Please try again."
                    st.error(str(e))
                st.session_state["messages"].append({"role": "assistant", "content": ai_reply})

    # --- Student input ---
    uploaded_audio = st.file_uploader(
        "Upload an audio file (WAV, MP3, OGG, M4A)",
        type=["wav", "mp3", "ogg", "m4a"],
        key="stage5_audio_upload"
    )
    typed_message = st.chat_input(
        "💬 Oder tippe deine Antwort hier...",
        key="stage5_typed_input"
    )
    user_input = None
    if uploaded_audio:
        uploaded_audio.seek(0)
        audio_bytes = uploaded_audio.read()
        st.audio(audio_bytes, format=uploaded_audio.type)
        try:
            suffix = "." + uploaded_audio.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
            client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp.name, "rb")
            )
            user_input = transcript.text
        except:
            st.warning("Transcription failed; please type your message.")
    elif typed_message:
        user_input = typed_message

    session_ended = st.session_state["turn_count"] >= max_turns
    used_today = st.session_state["daily_usage"][usage_key]
    ai_just_replied = False

    # --- Improved AI reply/grammar correction logic ---
    if user_input and not session_ended:
        if used_today >= DAILY_LIMIT:
            st.warning("You’ve reached today’s free practice limit. Please come back tomorrow or contact your tutor for unlimited access!")
        else:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1

            try:
                # --------- Choose prompt and context based on mode ----------
                if is_b1_teil3:
                    b1_topic = st.session_state.get("current_b1_teil3_topic", random.choice(B1_TEIL2))
                    ai_system_prompt = (
                        "You are Herr Felix, the examiner in a German B1 oral exam (Teil 3: Feedback & Questions). "
                        f"The topic of your presentation is: {b1_topic}. "
                        "The student is supposed to ask you TWO questions about your presentation and give you ONE positive feedback. "
                        "1. Read the student's message. "
                        "2. Tell the student if they have written two valid questions about the topic and one positive feedback (praise them if so, otherwise say politely what is missing). "
                        "3. If the questions are good, answer them briefly (in simple German). "
                        "4. Always end with clear encouragement in English. "
                        "Be friendly, supportive, and exam-like. Never break character."
                    )
                elif st.session_state.get("selected_mode", "") == "Eigenes Thema/Frage (Custom Topic Chat)":
                    ai_system_prompt = (
                        "You are Herr Felix, an expert German teacher and exam trainer. "
                        "Correct and give a grammar tip ONLY for the student's most recent answer, not for your own or earlier messages. "
                        "1. First, answer the student's message naturally as a German tutor (max 2–3 sentences). "
                        "2. Then, if there are mistakes, show the corrected sentence(s) clearly under 'Correction:'. "
                        "3. After that, give a very short 'Grammatik-Tipp:' in English with a simple explanation. "
                        "4. If the answer is perfect, say so and still give a tip in English. "
                        "5. Always end your message with a follow-up question or prompt to keep the conversation going. "
                        "Reply in this format:\n"
                        "- Your reply (German)\n- Correction: ...\n- Grammatik-Tipp: ...\n- Follow-up question (German)"
                    )
                else:
                    exam_level = st.session_state.get("selected_exam_level", "A2")
                    if exam_level == "A2":
                        ai_system_prompt = (
                            "You are Herr Felix, a strict but friendly Goethe A2 examiner. "
                            "Correct and give a grammar tip ONLY for the student's most recent answer, not for your own or earlier messages. "
                            "1. Answer the student's message in very simple A2-level German (max 2–3 sentences). "
                            "2. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                            "3. Give a short 'Grammatik-Tipp:' in English with a simple explanation. "
                            "4. If the answer is perfect, say so and still give a tip in English. "
                            "5. End with a follow-up question or prompt. "
                            "Format your reply:\n"
                            "- Your reply (German)\n- Correction: ...\n- Grammatik-Tipp: ...\n- Follow-up question (German)"
                        )
                    else:
                        ai_system_prompt = (
                            "You are Herr Felix, a strict but supportive Goethe B1 examiner. "
                            "Correct and give a grammar tip ONLY for the student's most recent answer, not for your own or earlier messages. "
                            "1. Answer the student's message in B1-level German (max 2–3 sentences). "
                            "2. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                            "3. Give a short 'Grammatik-Tipp:' in English. "
                            "4. If the answer is perfect, say so and still give a tip. "
                            "5. End with a follow-up question. "
                            "Format your reply:\n"
                            "- Your reply (German)\n- Correction: ...\n- Grammatik-Tipp: ...\n- Follow-up question (German)"
                        )

                # Only pass the latest user message for correction
                conversation = [
                    {"role": "system", "content": ai_system_prompt},
                    st.session_state["messages"][-1]
                ]

                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=conversation,
                )
                ai_reply = response.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response. Please try again."
                st.error(str(e))
            st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
            st.session_state["ai_audio"] = ai_reply
            ai_just_replied = True

    # --- Show chat history ---
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Herr Felix:</span> {msg['content']}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- Play audio for last AI message (if new) ---
    if ai_just_replied and "ai_audio" in st.session_state:
        try:
            tts = gTTS(st.session_state["ai_audio"], lang="de")
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.audio(buf.read(), format="audio/mp3")
        except:
            st.info("Audio feedback not available.")

    # --- Navigation ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
            st.session_state["step"] = prev
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
    with col2:
        if session_ended and st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6


    # --- Show chat history ---
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Herr Felix:</span> {msg['content']}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- Play audio for last AI message (if new) ---
    if ai_just_replied and "ai_audio" in st.session_state:
        try:
            tts = gTTS(st.session_state["ai_audio"], lang="de")
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.audio(buf.read(), format="audio/mp3")
        except:
            st.info("Audio feedback not available.")

    # --- Navigation ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
            st.session_state["step"] = prev
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
    with col2:
        if session_ended and st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6

# ------ Stage 6: Summary ------
if st.session_state["step"] == 6:
    st.title("🎉 Congratulations!")
    st.markdown(
        "<h3 style='color:#33691e;'>Session completed!</h3>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"**You completed {st.session_state['turn_count']} turns.**<br>"
        "Start again or choose another mode?",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Start New Session", key="stage6_restart"):
            st.session_state["step"] = 1
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["custom_topic"] = ""
    with col2:
        if st.button("⬅️ Back to Mode Selection", key="stage6_back"):
            st.session_state["step"] = 3
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
