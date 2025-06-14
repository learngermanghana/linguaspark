import os
import io
import re
import random
import tempfile
from datetime import date

import pandas as pd
import streamlit as st
from fpdf import FPDF
from gtts import gTTS
from openai import OpenAI


# Streamlit page config
st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---- Falowen / Herr Felix Header ----
st.markdown(
    """
    <div style='display:flex;align-items:center;gap:18px;margin-bottom:22px;'>
        <img src='https://cdn-icons-png.flaticon.com/512/6815/6815043.png' width='54' style='border-radius:50%;border:2.5px solid #51a8d2;box-shadow:0 2px 8px #cbe7fb;'/>
        <div>
            <span style='font-size:2.1rem;font-weight:bold;color:#17617a;letter-spacing:2px;'>Falowen</span><br>
            <span style='font-size:1.08rem;color:#268049;'>Your personal German speaking coach (Herr Felix)</span>
        </div>
    </div>
    """, unsafe_allow_html=True
)

# File/database constants
CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
max_turns = 6
TEACHER_PASSWORD = "Felix029"

# Exam topic lists
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
# STAGE 2: Teacher Area Sidebar & Session State Setup

# ---- Teacher Dashboard (Sidebar) ----
with st.sidebar.expander("👩‍🏫 Teacher Area (Login/Settings)", expanded=False):
    if "teacher_authenticated" not in st.session_state:
        st.session_state["teacher_authenticated"] = False

    # Teacher login prompt
    if not st.session_state["teacher_authenticated"]:
        st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
        pwd = st.text_input("Teacher Login (for admin only)", type="password")
        login_btn = st.button("Login (Teacher)")
        if login_btn:
            if pwd == TEACHER_PASSWORD:
                st.session_state["teacher_authenticated"] = True
                st.success("Access granted!")
            elif pwd != "":
                st.error("Incorrect password. Please try again.")

    # Teacher dashboard/settings
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

# ---- Global session state for app navigation ----
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
# STAGE 3: Student Login, Welcome, and Mode Selection

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
        [
            "Geführte Prüfungssimulation (Exam Mode)",
            "Eigenes Thema/Frage (Custom Topic Chat)",
            "Präsentationstraining (Presentation Practice)"
        ],
        index=0,
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage3_back"):
            st.session_state["step"] = 2
    with col2:
        if st.button("Next ➡️", key="stage3_next"):
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            if mode == "Geführte Prüfungssimulation (Exam Mode)":
                st.session_state["step"] = 4
            elif mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                st.session_state["step"] = 5
            elif mode == "Präsentationstraining (Presentation Practice)":
                st.session_state["step"] = 7  # <-- This triggers your new presentation practice tab
# ------ STAGE 4: Exam Part Selection ------
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
            # Select random topic and create the exam prompt
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
            # Store and advance to chat
            st.session_state["initial_prompt"] = prompt
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["step"] = 5


        
# ------ STAGE 5: Chat & Correction ------
def show_formatted_ai_reply(ai_reply):
    # Formatting for AI output: Answer, Correction, Grammar Tip (English), Next Question (German)
    import re
    lines = [l.strip() for l in ai_reply.split('\n') if l.strip()]
    main, correction, grammatik, followup = '', '', '', ''
    curr_section = 'main'

    for line in lines:
        header = line.lower()
        if header.startswith('correction:') or header.startswith('- correction:'):
            curr_section = 'correction'
            line = line.split(':',1)[-1].strip()
            if line: correction += line + ' '
            continue
        elif header.startswith('grammar tip:') or header.startswith('- grammar tip:') \
             or header.startswith('grammatik-tipp:') or header.startswith('- grammatik-tipp:'):
            curr_section = 'grammatik'
            line = line.split(':',1)[-1].strip()
            if line: grammatik += line + ' '
            continue
        elif header.startswith('next question:') or header.startswith('- next question:') \
             or header.startswith('follow-up question') or header.startswith('folgefrage'):
            curr_section = 'followup'
            line = line.split(':',1)[-1].strip()
            if line: followup += line + ' '
            continue
        if curr_section == 'main':
            main += line + ' '
        elif curr_section == 'correction':
            correction += line + ' '
        elif curr_section == 'grammatik':
            grammatik += line + ' '
        elif curr_section == 'followup':
            followup += line + ' '

    # In case the followup got stuck inside main/grammatik
    for block, setter in [(grammatik, 'grammatik'), (main, 'main')]:
        candidates = [l.strip() for l in block.split('\n') if l.strip()]
        if candidates:
            last = candidates[-1]
            if (last.endswith('?') or (last.endswith('.') and len(last.split()) < 14)) and not followup:
                followup = last
                if setter == 'grammatik':
                    grammatik = grammatik.replace(last, '').strip()
                else:
                    main = main.replace(last, '').strip()

    st.markdown(f"**📝 Answer:**  \n{main.strip()}", unsafe_allow_html=True)
    if correction.strip():
        st.markdown(f"<div style='color:#c62828'><b>✏️ Correction:</b>  \n{correction.strip()}</div>", unsafe_allow_html=True)
    if grammatik.strip():
        st.markdown(f"<div style='color:#1565c0'><b>📚 Grammar Tip:</b>  \n{grammatik.strip()}</div>", unsafe_allow_html=True)
    if followup.strip():
        st.markdown(f"<div style='color:#388e3c'><b>➡️ Next question:</b>  \n{followup.strip()}</div>", unsafe_allow_html=True)


# ------ STAGE 5 Logic ------
if st.session_state["step"] == 5:
    today_str    = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key    = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    st.info(
        f"Student code: `{student_code}` | "
        f"Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}"
    )

    is_b1_teil3 = (
        st.session_state.get("selected_mode", "").startswith("Geführte") and
        st.session_state.get("selected_exam_level") == "B1" and
        st.session_state.get("selected_teil", "").startswith("Teil 3")
    )

    # --- Custom Chat: Level selection comes first, no chat box yet ---
    if (
        st.session_state.get("selected_mode", "") == "Eigenes Thema/Frage (Custom Topic Chat)"
        and not st.session_state.get("custom_chat_level")
    ):
        level = st.radio(
            "Wähle dein Sprachniveau / Select your level:",
            ["A2", "B1"],
            horizontal=True,
            key="custom_level_select"
        )
        if st.button("Start Custom Chat"):
            st.session_state["custom_chat_level"] = level
            st.session_state["messages"] = [{
                "role": "assistant",
                "content": "Hallo! 👋 Worüber möchtest du heute sprechen oder üben? Schreib dein Präsentationsthema oder eine Frage."
            }]
        st.stop()  # Only runs until level is picked; after button, rerun shows chat UI

    # --- B1 Teil 3: First message
    if is_b1_teil3 and not st.session_state["messages"]:
        topic = random.choice(B1_TEIL2)
        st.session_state["current_b1_teil3_topic"] = topic
        init = (
            f"Ich habe gerade eine kurze Präsentation über **{topic}** gehalten.\n\n"
            "Deine Aufgabe jetzt:\n"
            "- Stelle mir **zwei Fragen** zu meiner Präsentation (auf Deutsch).\n"
            "- Gib mir **eine positive Rückmeldung** auf Deutsch.\n\n"
            "👉 Schreib deine zwei Fragen und ein Feedback jetzt unten auf!"
        )
        st.session_state["messages"].append({"role": "assistant", "content": init})

    # --- Custom Chat: Ensure greeting if messages is empty (safety)
    elif (
        st.session_state.get("selected_mode", "") == "Eigenes Thema/Frage (Custom Topic Chat)"
        and st.session_state.get("custom_chat_level")
        and not st.session_state["messages"]
    ):
        st.session_state["messages"].append({
            "role": "assistant",
            "content": "Hallo! 👋 Worüber möchtest du heute sprechen oder üben? Schreib dein Präsentationsthema oder eine Frage."
        })

    # --- Exam Mode: insert standard exam prompt
    elif (
        st.session_state.get("selected_mode", "").startswith("Geführte")
        and not st.session_state["messages"]
    ):
        prompt = st.session_state.get("initial_prompt")
        st.session_state["messages"].append({"role": "assistant", "content": prompt})

    # -- Student input (audio or text) --
    uploaded = st.file_uploader(
        "Upload an audio file (WAV, MP3, OGG, M4A)",
        type=["wav","mp3","ogg","m4a"],
        key="stage5_audio_upload"
    )
    typed = st.chat_input("💬 Oder tippe deine Antwort hier...", key="stage5_typed_input")
    user_input = None

    if uploaded:
        uploaded.seek(0)
        data = uploaded.read()
        st.audio(data, format=uploaded.type)
        try:
            suffix = "." + uploaded.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(data); tmp.flush()
            client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=open(tmp.name,"rb")
            )
            user_input = transcript.text
        except:
            st.warning("Transcription failed; please type your message.")
    elif typed:
        user_input = typed

    session_ended    = st.session_state["turn_count"] >= max_turns
    used_today       = st.session_state["daily_usage"][usage_key]
    ai_just_replied  = False

    # --- Build system prompt dynamically before OpenAI call ---
    if user_input and not session_ended:
        if used_today >= DAILY_LIMIT:
            st.warning(
                "You’ve reached today’s free practice limit. "
                "Please come back tomorrow or contact your tutor!"
            )
        else:
            st.session_state["messages"].append({"role":"user","content":user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1

            # SYSTEM PROMPT LOGIC
            if is_b1_teil3:
                b1_topic = st.session_state["current_b1_teil3_topic"]
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
            elif st.session_state["selected_mode"] == "Eigenes Thema/Frage (Custom Topic Chat)":
                lvl = st.session_state.get("custom_chat_level", "A2")
                if lvl == "A2":
                    ai_system_prompt = (
                        "You are Herr Felix, a friendly but strict A2 German teacher and exam trainer. "
                        "Reply at A2-level, using simple German sentences. "
                        "Correct and give a short grammar tip ONLY for the student's most recent answer (always in English). "
                        "Your reply format:\n"
                        "- Your answer (German)\n"
                        "- Correction (if needed, in German)\n"
                        "- Grammar Tip (in English, one short sentence)\n"
                        "- Next question (in German)\n"
                    )
                else:
                    ai_system_prompt = (
                        "You are Herr Felix, a supportive B1 German teacher and exam trainer. "
                        "Reply at B1-level in German. "
                        "Correct and give a grammar tip for the student's last answer (always in English). "
                        "Your reply format:\n"
                        "- Your answer (German)\n"
                        "- Correction (if needed, in German)\n"
                        "- Grammar Tip (in English, one short sentence)\n"
                        "- Next question (in German)\n"
                    )
            else:
                lvl = st.session_state["selected_exam_level"]
                if lvl == "A2":
                    ai_system_prompt = (
                        "You are Herr Felix, a strict but friendly Goethe A2 examiner. "
                        "Correct and give a grammar tip ONLY for the student's most recent answer, not for your own or earlier messages. "
                        "1. Answer the student's message in very simple A2-level German (max 2–3 sentences). "
                        "2. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                        "3. Give a short grammar tip (in English, one short sentence). "
                        "4. If the answer is perfect, say so and still give a tip in English. "
                        "5. End with a next question or prompt in German. "
                        "Format your reply:\n"
                        "- Your answer (German)\n- Correction: ...\n- Grammar Tip: ...\n- Next question (German)"
                    )
                else:
                    ai_system_prompt = (
                        "You are Herr Felix, a strict but supportive Goethe B1 examiner. "
                        "Correct and give a grammar tip ONLY for the student's most recent answer, not for your own or earlier messages. "
                        "1. Answer the student's message in B1-level German (max 2–3 sentences). "
                        "2. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                        "3. Give a short grammar tip (in English, one short sentence). "
                        "4. If the answer is perfect, say so and still give a tip in English. "
                        "5. End with a next question or prompt in German. "
                        "Format your reply:\n"
                        "- Your answer (German)\n- Correction: ...\n- Grammar Tip: ...\n- Next question (German)"
                    )

            # --- Call OpenAI with only the last user message ---
            conversation = [
                {"role":"system","content":ai_system_prompt},
                st.session_state["messages"][-1]
            ]
            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp   = client.chat.completions.create(
                    model="gpt-4o", messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))

            st.session_state["messages"].append(
                {"role":"assistant","content":ai_reply}
            )
            ai_just_replied = True

    # --- Render chat history with formatted AI replies ---
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(
                    "<span style='color:#33691e;font-weight:bold'>🧑‍🏫 Herr Felix:</span>",
                    unsafe_allow_html=True
                )
                show_formatted_ai_reply(msg["content"])
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- Navigation buttons (single instance) ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
            st.session_state.update({
                "step":prev,
                "messages":[],
                "turn_count":0,
                "custom_chat_level":None,
                "custom_level_prompted":False,
            })
    with col2:
        if session_ended and st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6


# STAGE 6: Session Summary & Restart

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


# stage 7: Module-level configuration for default session state
STATE_DEFAULTS = {
    "presentation_step": 0,
    "presentation_level": None,
    "presentation_topic": "",
    "a2_keywords": None,
    "a2_keyword_progress": [],  # track covered keywords as a list
    "presentation_messages": [],
    "presentation_turn_count": 0,
    "b1_init_done": False,
    "awaiting_ai_reply": False
}

# Bottom button configurations
action_buttons = [
    {"label": "🔄 Restart Practice", "reset_keys": list(STATE_DEFAULTS.keys()), "set_step": None},
    {"label": "📝 Change Topic", "reset_keys": ["presentation_messages", "presentation_turn_count", "awaiting_ai_reply", "b1_init_done", "a2_keyword_progress"], "set_step": 1},
    {"label": "🔧 Change Level", "reset_keys": list(STATE_DEFAULTS.keys()), "set_step": 0},
]


def initialize_state(defaults=STATE_DEFAULTS):
    for k, v in defaults.items():
        if isinstance(v, list):
            st.session_state.setdefault(k, v.copy())
        else:
            st.session_state.setdefault(k, v)


def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass


def reset_state(keys):
    for k in keys:
        st.session_state.pop(k, None)


def handle_level_selection():
    level = st.radio("Select your level:", ["A2", "B1"], horizontal=True)
    if st.button("Start Presentation Practice"):
        st.session_state.presentation_level = level
        st.session_state.presentation_step = 1
        reset_state(["presentation_messages", "presentation_turn_count", "a2_keywords", "a2_keyword_progress", "b1_init_done", "awaiting_ai_reply"])
        safe_rerun()


def handle_topic_input():
    st.info("Write a short sentence for your presentation topic (English or German).")
    topic = st.text_input("Presentation topic:", key="topic_input")
    if st.button("Submit Topic") and topic.strip():
        st.session_state.presentation_topic = topic.strip()
        st.session_state.presentation_messages = [{"role": "user", "content": topic.strip()}]
        st.session_state.presentation_step = 2 if st.session_state.presentation_level == "A2" else 3
        st.session_state.awaiting_ai_reply = True
        st.session_state.b1_init_done = False
        st.session_state.a2_keyword_progress = []
        safe_rerun()


def handle_keywords_input():
    st.info("Enter 3–4 German keywords separated by commas.")
    topic = st.session_state.presentation_topic or "Ihres Themas"
    st.caption(f"Beispiel: 'Familie, Freunde, Hobby, Arbeit' basierend auf {topic}.")
    kws = st.text_input("Keywords (comma-separated):", key="keywords_input")
    if st.button("Submit Keywords"):
        arr = [kw.strip() for kw in kws.split(",") if kw.strip()]
        if len(arr) >= 3:
            st.session_state.a2_keywords = arr[:4]
            st.session_state.presentation_step = 3
            st.session_state.awaiting_ai_reply = True
            st.session_state.a2_keyword_progress = []
            safe_rerun()
        else:
            st.warning("Please enter at least 3 keywords.")


def render_progress_bar():
    max_turns = 8
    level = st.session_state.presentation_level
    if level == "A2":
        kws = st.session_state.a2_keywords or []
        total = len(kws)
        done = len(st.session_state.a2_keyword_progress)
        ratio = done / total if total else 0
        label = " | ".join([
            f"✅ {kw}" if kw in st.session_state.a2_keyword_progress else f"⬜ {kw}" for kw in kws
        ])
        st.progress(ratio)
        st.markdown(f"**Progress:** {label}")
        st.markdown("---")
    else:
        total = max_turns
        done = st.session_state.presentation_turn_count
        ratio = done / total
        label = f"Turn {done} of {total}"
        st.progress(ratio)
        st.markdown(f"**Progress:** {label}")
        st.markdown("---")


def build_system_prompt():
    level = st.session_state.presentation_level
    topic = st.session_state.presentation_topic
    if level == 'A2':
        kws = st.session_state.a2_keywords or []
        used = st.session_state.a2_keyword_progress
        next_kw = next((kw for kw in kws if kw not in used), None) or (kws[-1] if kws else "(no keywords)")
        return f"You are Herr Felix, an A2 teacher. Focus on keyword '{next_kw}'. Provide an English suggestion sentence using it, a German example sentence, a sentence starter, an English correction, and then ask a follow-up question in German using this keyword."
    else:
        if not st.session_state.b1_init_done:
            st.session_state.b1_init_done = True
            return f"You are Herr Felix, a B1 teacher. Provide structure and ideas for '{topic}': introduction, main points, conclusion, connectors. Then ask the first follow-up question in German about this topic."
        return f"You are Herr Felix, a B1 teacher. Student presenting on '{topic}'. Based on their last answer, ask the next relevant question in German tied to the topic and give brief English feedback."


def handle_chat_loop():
    if st.session_state.awaiting_ai_reply:
        st.session_state.awaiting_ai_reply = False
        prompt = build_system_prompt()
        last_user = next((m for m in reversed(st.session_state.presentation_messages) if m['role']=='user'), None)
        if last_user:
            with st.spinner("Thinking..."):
                try:
                    resp = OpenAI(api_key=st.secrets['general']['OPENAI_API_KEY']).chat.completions.create(model='gpt-4o', messages=[{'role':'system','content':prompt}, last_user])
                    ai_text = resp.choices[0].message.content
                except Exception:
                    ai_text = "Sorry, something went wrong."
            st.session_state.presentation_messages.append({'role':'assistant','content':ai_text})
            safe_rerun()

    render_progress_bar()
    for msg in st.session_state.presentation_messages:
        with st.chat_message(msg['role'], avatar='🧑‍🏫' if msg['role']=='assistant' else None):
            prefix = '🧑‍🏫 Herr Felix:' if msg['role']=='assistant' else '🗣️'
            st.markdown(f"{prefix} {msg['content']}")

    if st.session_state.presentation_step >= 3:
        user_msg = st.chat_input(f"💬 Antwort zum Thema '{st.session_state.presentation_topic}'...", key="chat_input")
        if user_msg:
            st.session_state.presentation_messages.append({"role": "user", "content": user_msg})
            st.session_state.presentation_turn_count += 1
            if st.session_state.presentation_level == "A2":
                for kw in (st.session_state.a2_keywords or []):
                    if kw.lower() in user_msg.lower() and kw not in st.session_state.a2_keyword_progress:
                        st.session_state.a2_keyword_progress.append(kw)
            st.session_state.awaiting_ai_reply = True


def stage_7():
    initialize_state()
    st.header("🎤 Presentation Practice (A2 & B1)")

    stage = st.session_state.presentation_step
    if stage == 0:
        handle_level_selection()
    elif stage == 1:
        handle_topic_input()
    elif stage == 2:
        handle_keywords_input()
    else:
        handle_chat_loop()

    if st.session_state.presentation_step >= 3:
        if st.session_state.presentation_level == "A2":
            done = len(st.session_state.a2_keyword_progress) == len(st.session_state.a2_keywords or [])
        else:
            done = st.session_state.presentation_turn_count >= 8
        if done:
            st.success("🎉 Practice complete! 🎉")
            final = "\n\n".join([f"👤 {m['content']}" if m['role']=='user' else f"🧑‍🏫 {m['content']}" for m in st.session_state.presentation_messages])
            st.subheader("📄 Your Final Presentation")
            st.markdown(final)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in final.split("\n\n"):
                safe_line = line.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, safe_line)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Download PDF", data=pdf_bytes, file_name="Presentation_Practice.pdf")
            return

    cols = st.columns(len(action_buttons))
    for i, btn in enumerate(action_buttons):
        if cols[i].button(btn['label']):
            if btn['set_step'] is not None:
                st.session_state.presentation_step = btn['set_step']
            reset_state(btn['reset_keys'])
            safe_rerun()

stage_7()
