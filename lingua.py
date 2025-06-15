# === STAGE 1: Imports & Config ===
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

def safe_rerun():
    st.experimental_rerun()

st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="expanded"
)

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

# === STAGE 2: Global State Initialization ===

CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
max_turns = 6
TEACHER_PASSWORD = "Felix029"

A2_TEIL1 = [
    "Wohnort", "Tagesablauf", "Freizeit", "Sprachen", "Essen & Trinken", "Haustiere",
    "Lieblingsmonat", "Jahreszeit", "Sport", "Kleidung (Sommer)", "Familie", "Beruf",
    "Hobbys", "Feiertage", "Reisen", "Lieblingsessen", "Schule", "Wetter", "Auto oder Fahrrad", "Perfekter Tag"
]
A2_TEIL2 = [
    "Was machen Sie mit Ihrem Geld?", "Was machen Sie am Wochenende?", "Wie verbringen Sie Ihren Urlaub?",
    "Wie oft gehen Sie einkaufen und was kaufen Sie?", "Was für Musik hören Sie gern?", "Wie feiern Sie Ihren Geburtstag?",
    "Welche Verkehrsmittel nutzen Sie?", "Wie bleiben Sie gesund?", "Was machen Sie gern mit Ihrer Familie?",
    "Wie sieht Ihr Traumhaus aus?", "Welche Filme oder Serien mögen Sie?", "Wie oft gehen Sie ins Restaurant?",
    "Was ist Ihr Lieblingsfeiertag?", "Was machen Sie morgens als Erstes?", "Wie lange schlafen Sie normalerweise?",
    "Welche Hobbys hatten Sie als Kind?", "Machen Sie lieber Urlaub am Meer oder in den Bergen?",
    "Wie sieht Ihr Lieblingszimmer aus?", "Was ist Ihr Lieblingsgeschäft?", "Wie sieht ein perfekter Tag für Sie aus?"
]
A2_TEIL3 = [
    "Zusammen ins Kino gehen", "Ein Café besuchen", "Gemeinsam einkaufen gehen",
    "Ein Picknick im Park organisieren", "Eine Fahrradtour planen", "Zusammen in die Stadt gehen",
    "Einen Ausflug ins Schwimmbad machen", "Eine Party organisieren", "Zusammen Abendessen gehen",
    "Gemeinsam einen Freund/eine Freundin besuchen", "Zusammen ins Museum gehen", "Einen Spaziergang im Park machen",
    "Ein Konzert besuchen", "Zusammen eine Ausstellung besuchen", "Einen Wochenendausflug planen",
    "Ein Theaterstück ansehen", "Ein neues Restaurant ausprobieren", "Einen Kochabend organisieren",
    "Einen Sportevent besuchen", "Eine Wanderung machen"
]
B1_TEIL1 = [
    "Mithilfe beim Sommerfest", "Eine Reise nach Köln planen", "Überraschungsparty organisieren",
    "Kulturelles Ereignis (Konzert, Ausstellung) planen", "Museumsbesuch organisieren"
]
B1_TEIL2 = [
    "Ausbildung", "Auslandsaufenthalt", "Behinderten-Sport", "Berufstätige Eltern", "Berufswahl", "Bio-Essen",
    "Chatten", "Computer für jeden Kursraum", "Das Internet", "Einkaufen in Einkaufszentren", "Einkaufen im Internet",
    "Extremsport", "Facebook", "Fertigessen", "Freiwillige Arbeit", "Freundschaft", "Gebrauchte Kleidung",
    "Getrennter Unterricht für Jungen und Mädchen", "Haushalt", "Haustiere", "Heiraten", "Hotel Mama",
    "Ich bin reich genug", "Informationen im Internet", "Kinder und Fernsehen", "Kinder und Handys", "Kinos sterben",
    "Kreditkarten", "Leben auf dem Land oder in der Stadt", "Makeup für Kinder", "Marken-Kleidung", "Mode",
    "Musikinstrument lernen", "Musik im Zeitalter des Internets", "Rauchen", "Reisen", "Schokolade macht glücklich",
    "Sport treiben", "Sprachenlernen", "Sprachenlernen mit dem Internet", "Stadtzentrum ohne Autos",
    "Studenten und Arbeit in den Ferien", "Studium", "Tattoos", "Teilzeitarbeit", "Unsere Idole", "Umweltschutz",
    "Vegetarische Ernährung", "Zeitungslesen"
]
B1_TEIL3 = [
    "Fragen stellen zu einer Präsentation", "Positives Feedback geben", "Etwas überraschend finden oder planen",
    "Weitere Details erfragen"
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

defaults = {
    "step": 1, "student_code": "", "daily_usage": {},
    "messages": [], "corrections": [], "turn_count": 0,
    "presentation_step": 0, "presentation_level": None, "presentation_topic": "",
    "a2_keywords": None, "a2_keyword_progress": set(),
    "presentation_messages": [], "presentation_turn_count": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v.copy() if isinstance(v, (list, set, dict)) else v

# === STAGE 3: Login Stage ===
def stage_1():
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

# === STAGE 4: Welcome Stage ===
def stage_2():
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
    if st.button("Next ➡️"):
        st.session_state["step"] = 3
# === STAGE 5: Mode Selection Stage ===
def stage_3():
    st.header("Select mode")
    mode = st.radio(
        "Choose your practice mode:",
        [
            "Geführte Prüfungssimulation (Exam Mode)",
            "Eigenes Thema/Frage (Custom Topic Chat)",
            "Präsentationstraining (Presentation Practice)"
        ],
        index=0
    )
    st.session_state["selected_mode"] = mode
    if st.button("Start"):
        if mode == "Präsentationstraining (Presentation Practice)":
            st.session_state["step"] = 7
        else:
            st.session_state["step"] = 4
# === STAGE 6: Exam/Custom Chat/Summary ===

def show_formatted_ai_reply(ai_reply):
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

def stage_4_5_6():
    # ---- STAGE 4: Exam Part Selection ----
    if st.session_state["step"] == 4:
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
    elif st.session_state["step"] == 5:
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
            st.stop()

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

        elif (
            st.session_state.get("selected_mode", "") == "Eigenes Thema/Frage (Custom Topic Chat)"
            and st.session_state.get("custom_chat_level")
            and not st.session_state["messages"]
        ):
            st.session_state["messages"].append({
                "role": "assistant",
                "content": "Hallo! 👋 Worüber möchtest du heute sprechen oder üben? Schreib dein Präsentationsthema oder eine Frage."
            })

        elif (
            st.session_state.get("selected_mode", "").startswith("Geführte")
            and not st.session_state["messages"]
        ):
            prompt = st.session_state.get("initial_prompt")
            st.session_state["messages"].append({"role": "assistant", "content": prompt})

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

    # ------ STAGE 6: Session Summary & Restart ------
    elif st.session_state["step"] == 6:
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


# === STAGE 7: Presentation Practice ===

def safe_rerun():
    import streamlit as st
    st.experimental_rerun()


def presentation_keywords_input(safe_rerun):
    """Prompt user for keywords in A2 presentation."""
    if st.session_state.presentation_step == 2:
        st.info(
            "Enter 3–4 German keywords, comma-separated.\n\n"
            "Example: **Schule, Hausaufgaben, Lehrer, Prüfung**"
        )
        kw = st.text_input("Keywords:", key="kw_input")
        if st.button("Submit Keywords"):
            arr = [x.strip() for x in kw.split(',') if x.strip()]
            if len(arr) >= 3:
                st.session_state.a2_keywords = arr[:4]
                st.session_state.presentation_step = 3
                safe_rerun()
            else:
                st.warning("Enter at least 3 keywords.")
        return

def presentation_chat_loop(generate_ai_reply_and_rerun, safe_rerun):
    if st.session_state.presentation_step != 3:
        return

    msgs = st.session_state.presentation_messages

    # --- AUTO-START: AI replies if chat is empty or last is user ---
    need_ai = (
        not msgs or
        (msgs and msgs[-1]['role'] == 'user' and (len(msgs) < 2 or msgs[-2]['role'] != 'assistant'))
    )
    if need_ai:
        generate_ai_reply_and_rerun()

    # --- SPEECH BUBBLES: Show chat history ---
    for m in st.session_state.presentation_messages:
        if m['role'] == 'user':
            st.markdown(
                f"""
                <div style='display:flex;align-items:flex-start;margin-bottom:10px;'>
                  <div style='background:#e3f2fd;color:#1565c0;padding:0.7em 1em;border-radius:1em 1em 1em 0;max-width:80%;display:inline-block;'>
                    <b>👤</b> {m['content']}
                  </div>
                </div>
                """, unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style='display:flex;justify-content:flex-end;margin-bottom:10px;'>
                  <div style='background:#e8f5e9;color:#2e7d32;padding:0.7em 1em;border-radius:1em 1em 0 1em;max-width:80%;display:inline-block;'>
                    <b>🧑‍🏫 Herr Felix:</b> {m['content']}
                  </div>
                </div>
                """, unsafe_allow_html=True
            )

    # --- INPUT ---
    inp = st.chat_input("Type your response...")
    if inp:
        today = str(date.today())
        code = st.session_state.get("student_code", "(unknown)")
        key = f"{code}_{today}"
        if 'daily_usage' in st.session_state and key in st.session_state['daily_usage']:
            st.session_state['daily_usage'][key] += 1
        st.session_state.presentation_messages.append({'role': 'user', 'content': inp})
        st.session_state.presentation_turn_count += 1
        if st.session_state.presentation_level == 'A2':
            for k in st.session_state.a2_keywords or []:
                if k.lower() in inp.lower():
                    st.session_state.a2_keyword_progress.add(k)
        generate_ai_reply_and_rerun()

    # --- PROGRESS & CONTROLS ---
    max_turns = 12
    done = st.session_state.presentation_turn_count
    st.progress(min(done / max_turns, 1.0))
    st.markdown(f"**Progress:** Turn {done}/{max_turns}")
    st.markdown("---")

    a2_done = (st.session_state.presentation_level == 'A2' and done >= max_turns)
    b1_done = (st.session_state.presentation_level == 'B1' and done >= max_turns)
    if a2_done or b1_done:
        st.success("Practice complete! 🎉")
        lines = [
            f"👤 {m['content']}" if m['role'] == 'user' else f"🧑‍🏫 {m['content']}"
            for m in st.session_state.presentation_messages
        ]
        st.subheader("Your Session Summary")
        st.markdown("\n\n".join(lines))

        # --- Controls: Restart, Change Topic, Change Level ---
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔁 Restart Practice"):
                for k in [
                    'presentation_step', 'presentation_messages', 'presentation_turn_count',
                    'a2_keywords', 'a2_keyword_progress'
                ]:
                    st.session_state.pop(k, None)
                safe_rerun()
        with col2:
            if st.button("✏️ Change Topic"):
                st.session_state["presentation_step"] = 1
                st.session_state["presentation_topic"] = ""
                st.session_state["presentation_messages"] = []
                safe_rerun()
        with col3:
            if st.button("⬆️ Change Level"):
                for k in [
                    'presentation_step', 'presentation_level', 'presentation_topic',
                    'presentation_messages', 'presentation_turn_count',
                    'a2_keywords', 'a2_keyword_progress'
                ]:
                    st.session_state.pop(k, None)
                st.session_state["presentation_step"] = 0
                safe_rerun()

def generate_ai_reply_and_rerun():
    placeholder = st.empty()
    placeholder.info("🧑‍🏫 Herr Felix is typing...")

    if st.session_state.presentation_level == 'A2':
        kws = list(st.session_state.a2_keywords or [])
        topic = st.session_state.presentation_topic
        next_kw = next((kw for kw in kws if kw not in st.session_state.a2_keyword_progress), kws[0] if kws else "")
        system = (
            f"You are Herr Felix, an intelligent and friendly German A2 teacher. "
            f"You are helping a student practice for an upcoming German presentation. "
            f"Always keep the conversation focused on the topic '{topic}' and the keywords: {', '.join(kws)}. "
            f"Right now, focus especially on the keyword '{next_kw}'. "
            "You must always use only A2-level vocabulary and grammar in your questions, examples, and corrections. "
            "Avoid long, complex sentences or rare words. "
            "Whenever possible, include the current keyword in your question or model answer. "
            "Your goal is to guide the student to prepare, structure, and expand their presentation answers. "
            "Ask questions that help them give better, fuller answers and practice what they'll say. "
            "If they make mistakes, explain the correction in simple English so the student understands. "
            "Always give examples and tips in English if needed, but your next question should always be in German. "
            "Do not move to a new topic or keyword until the current one has been covered well. "
            "Act as both a helpful coach and a chat partner—encourage, teach, and help them improve for their real presentation!"
        )
    else:
        topic = st.session_state.presentation_topic
        steps = [
            f"You are Herr Felix, a motivating B1 teacher. Only discuss the student topic: '{topic}'. Ask for the student's opinion in German. Give positive feedback in English. If you correct a sentence, explain the correction in English.",
            f"Still discussing '{topic}'. Now share your opinion in German and ask the student to respond. Feedback/corrections always in English.",
            f"Keep to the topic '{topic}'. Ask the student to list advantages and disadvantages in German. Any explanations/corrections in English.",
            f"Relate topic '{topic}' to student's home country in German. Feedback/corrections in English.",
            f"Ask for a conclusion or recommendation in German about '{topic}'. Cheer in English.",
            f"Summarize student's points in German and highlight progress. Explanations/corrections in English.",
            f"Ask the student to tell a personal story about '{topic}' in German. Feedback/corrections in English.",
            f"Ask for a comparison: How is '{topic}' different in Germany vs. student's country? (German). Corrections/tips in English.",
            f"Invite the student to ask you a question about '{topic}' in German. Respond and explain in English.",
            f"Ask the student for a summary or key learning about '{topic}' in German. Encourage in English.",
            f"Conclude with a final opinion on '{topic}' in German. Give closing positive feedback in English.",
            f"Ask: What is your advice for someone interested in '{topic}'? (German). Cheer in English.",
        ]
        idx = min(st.session_state.presentation_turn_count, len(steps)-1)
        system = steps[idx]

    last = st.session_state.presentation_messages[-1] if st.session_state.presentation_messages else None
    messages = [{'role':'system','content':system}]
    if last:
        messages.append(last)

    try:
        resp = OpenAI(api_key=st.secrets['general']['OPENAI_API_KEY']).chat.completions.create(
            model='gpt-4o', messages=messages
        )
        reply = resp.choices[0].message.content
    except Exception:
        reply = "Sorry, something went wrong."

    placeholder.empty()
    st.session_state.presentation_messages.append({'role':'assistant','content':reply})
    safe_rerun()

def stage_7():
    # Ensure all session keys exist
    defaults = {
        "presentation_step": 0,
        "presentation_level": None,
        "presentation_topic": "",
        "a2_keywords": None,
        "a2_keyword_progress": set(),
        "presentation_messages": [],
        "presentation_turn_count": 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v.copy() if isinstance(v, (list, set, dict)) else v

    st.header("🎤 Presentation Practice")

    # --- Level selection (A2 or B1) ---
    if st.session_state.presentation_step == 0:
        lvl = st.radio("Select your level:", ["A2", "B1"], horizontal=True)
        if st.button("Start Presentation Practice"):
            st.session_state.presentation_level = lvl
            st.session_state.presentation_step = 1
            st.session_state.presentation_messages.clear()
            st.session_state.presentation_turn_count = 0
            st.session_state.a2_keywords = None
            st.session_state.a2_keyword_progress = set()
            st.session_state.presentation_topic = ""
            safe_rerun()
        return

    # --- Topic input ---
    if st.session_state.presentation_step == 1:
        st.info("Please enter your presentation topic (English or German). 🔖")
        t = st.text_input("Topic:", key="topic_input")
        if st.button("Submit Topic") and t:
            st.session_state.presentation_topic = t
            st.session_state.presentation_messages.append({'role':'user','content':t})
            st.session_state.presentation_step = 2 if st.session_state.presentation_level == 'A2' else 3
            safe_rerun()
        return

    # --- Keyword input (A2 only) ---
    if st.session_state.presentation_level == "A2" and st.session_state.presentation_step == 2:
        presentation_keywords_input(safe_rerun)
        return

    # --- Chat loop (A2/B1) ---
    if st.session_state.presentation_step == 3:
        presentation_chat_loop(generate_ai_reply_and_rerun, safe_rerun)
        return


# ---- Main navigation ----
if "step" not in st.session_state:
    st.session_state["step"] = 1

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
elif st.session_state["step"] == 2:
    st.header("🧑‍🏫 Welcome!")
    if st.button("Next ➡️"):
        st.session_state["step"] = 3
elif st.session_state["step"] == 3:
    st.header("Select mode")
    mode = st.radio(
        "Choose your practice mode:",
        [
            "Geführte Prüfungssimulation (Exam Mode)",
            "Eigenes Thema/Frage (Custom Topic Chat)",
            "Präsentationstraining (Presentation Practice)"
        ],
        index=0
    )
    st.session_state["selected_mode"] = mode
    if st.button("Start"):
        if mode == "Präsentationstraining (Presentation Practice)":
            st.session_state["step"] = 7
        else:
            st.session_state["step"] = 4
elif st.session_state["step"] == 7:
    stage_7()

