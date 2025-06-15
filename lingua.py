# ===============================
#         STAGE 1: IMPORTS, CONSTANTS, HELPERS
# ===============================
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

# For responsive UI (used in chat logic)
from streamlit.runtime.scriptrunner import add_script_run_ctx
import threading
import time

# --------------------------
CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
MAX_TURNS = 6

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

def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass

# ===============================
#         STAGE 2: PAGE CONFIG & HEADER & INIT STATE
# ===============================
def setup_ui_and_state():
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
                <span style='font-size:1.08rem;color:#268049;'>Your personal German speaking coach (Sir Felix)</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    for var, default in [
        ("step", 1), ("student_code", ""), ("daily_usage", {}), ("messages", []),
        ("corrections", []), ("turn_count", 0)
    ]:
        if var not in st.session_state:
            st.session_state[var] = default

# ===============================
#         STAGE 3: STUDENT LOGIN, WELCOME, MODE SELECTION
# ===============================
def stage_3_login_and_mode():
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
            "🇬🇭 Sir Felix was born in Ghana and mastered German up to C1 level!",
            "🎓 Sir Felix studied International Management at IU International University in Germany.",
            "🏫 He founded Learn Language Education Academy to help students pass Goethe exams.",
            "💡 Sir Felix used to run a record label and produce music before becoming a language coach!",
            "🥇 He loves making language learning fun, personal, and exam-focused.",
            "📚 Sir Felix speaks English, German, and loves teaching in both.",
            "🚀 Sometimes Sir Felix will throw in a real Goethe exam question—are you ready?",
            "🤖 Sir Felix built this app himself—so every session is personalized!"
        ]
        st.success(f"**Did you know?** {random.choice(fun_facts)}")
        st.markdown(
            "<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor, Sir Felix!</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("> Practice your German speaking or writing. Get simple AI feedback and audio answers!")
        st.info(
            """
            🎤 **This is not just chat—it's your personal exam preparation bootcamp!**
            Every time you talk to Sir Felix, imagine you are **in the exam hall**.
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
                    st.session_state["step"] = 7

# ===============================
#         STAGE 4: EXAM PART SELECTION
# ===============================
def stage_4_exam_part():
    if st.session_state["step"] != 4:
        return
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

# ===============================
#         STAGE 5: LIVE, STYLED CHAT (APPLIES TO EXAM/CUSTOM MODES)
# ===============================
def stage_5_chat():
    # Only run for stage 5!
    if st.session_state.get("step") != 5:
        return

    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    st.markdown(
        f"<div style='margin-bottom:0.5em'>"
        f"<span style='background:#bee3f8;border-radius:0.5em;padding:0.3em 0.8em;'>"
        f"Student code: <b>{student_code}</b> &nbsp; | &nbsp; Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}"
        f"</span></div>",
        unsafe_allow_html=True
    )

    def show_formatted_ai_reply(ai_reply):
        lines = [l.strip() for l in ai_reply.split('\n') if l.strip()]
        answer, correction, explanation, followup = '', '', '', ''
        curr = 'answer'
        for line in lines:
            header = line.lower()
            if 'correction:' in header:
                curr = 'correction'
                line = line.split(':', 1)[-1].strip()
            elif 'grammar tip:' in header or 'explanation:' in header or 'tip:' in header:
                curr = 'explanation'
                line = line.split(':', 1)[-1].strip()
            elif 'next question:' in header or 'follow-up' in header:
                curr = 'followup'
                line = line.split(':', 1)[-1].strip()
            if curr == 'answer':
                answer += line + ' '
            elif curr == 'correction':
                correction += line + ' '
            elif curr == 'explanation':
                explanation += line + ' '
            elif curr == 'followup':
                followup += line + ' '

        if answer.strip():
            st.markdown(f"<div style='font-size:1.05em;line-height:1.6'><b>Answer:</b><br>{answer.strip()}</div>", unsafe_allow_html=True)
        if correction.strip():
            st.markdown(f"<div style='color:#ea574b'><b>Correction (English):</b><br>{correction.strip()}</div>", unsafe_allow_html=True)
        if explanation.strip():
            st.markdown(f"<div style='color:#375be3'><b>Explanation (English):</b><br>{explanation.strip()}</div>", unsafe_allow_html=True)
        if followup.strip():
            st.markdown(f"<div style='color:#32a852'><b>Next Question:</b><br>{followup.strip()}</div>", unsafe_allow_html=True)

    def render_chat():
        for i, msg in enumerate(st.session_state["messages"]):
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🧑‍🏫"):
                    st.markdown("""
                    <div style='display:flex;flex-direction:row-reverse;align-items:flex-end;'>
                      <div style='background:linear-gradient(90deg,#bee3f8,#98f5e1);color:#174562;padding:1em 1.2em;margin:6px 0 6px 64px;border-radius:1.1em 1.1em 0.1em 1.1em;max-width:65vw;min-width:110px;box-shadow:0 1px 6px #d9ecfa;'>
                        <b>Sir Felix</b><br>
                        """, unsafe_allow_html=True)
                    show_formatted_ai_reply(msg["content"])
                    st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown("""
                    <div style='display:flex;flex-direction:row;align-items:flex-end;'>
                      <div style='background:#f1f1f1;color:#181818;padding:1em 1.2em;margin:6px 64px 6px 0;border-radius:1.1em 1.1em 1.1em 0.1em;max-width:65vw;min-width:110px;box-shadow:0 1px 4px #e5e5e5;'>
                        <b>Student</b><br>
                    """, unsafe_allow_html=True)
                    st.markdown(msg["content"])
                    st.markdown("</div></div>", unsafe_allow_html=True)

    render_chat()

    # --- Input form (always shows) ---
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your reply or exam answer here...", height=70)
        submitted = st.form_submit_button("Send")

    session_ended = st.session_state["turn_count"] >= MAX_TURNS
    used_today = st.session_state["daily_usage"][usage_key]

    if submitted and user_input and not session_ended:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["turn_count"] += 1
        st.session_state["daily_usage"][usage_key] += 1

        with st.spinner("Sir Felix is typing..."):
            # SYSTEM PROMPT LOGIC
            if st.session_state.get("selected_mode") == "Eigenes Thema/Frage (Custom Topic Chat)":
                lvl = st.session_state.get("custom_chat_level", "A2")
                if lvl == "A2":
                    system_prompt = (
                        "You are Sir Felix, a friendly but strict A2 German teacher and exam trainer. "
                        "ALWAYS give corrections and grammar explanations in ENGLISH, no matter what the student writes. "
                        "Reply at A2-level, using simple German sentences. "
                        "Correct and give a short grammar tip ONLY for the student's most recent answer (always in English). "
                        "Your reply format:\n"
                        "- Your answer (German)\n"
                        "- Correction (in English, if needed)\n"
                        "- Explanation (in English)\n"
                        "- Next question (in German)\n"
                    )
                else:
                    system_prompt = (
                        "You are Sir Felix, a supportive B1 German teacher and exam trainer. "
                        "ALWAYS give corrections and grammar explanations in ENGLISH. "
                        "Reply at B1-level in German. "
                        "Correct and give a grammar tip for the student's last answer (always in English). "
                        "Your reply format:\n"
                        "- Your answer (German)\n"
                        "- Correction (in English)\n"
                        "- Explanation (in English)\n"
                        "- Next question (in German)\n"
                    )
            else:
                lvl = st.session_state["selected_exam_level"]
                if lvl == "A2":
                    system_prompt = (
                        "You are Sir Felix, a strict but friendly Goethe A2 examiner. "
                        "ALWAYS correct and explain in ENGLISH only. "
                        "1. Answer the student's message in very simple A2-level German (max 2–3 sentences). "
                        "2. If there are mistakes, show the corrected sentence(s) under 'Correction:' (in English). "
                        "3. Give a short grammar explanation (in English). "
                        "4. If the answer is perfect, say so and still give a tip in English. "
                        "5. End with a next question or prompt in German."
                        "Format your reply:\n"
                        "- Your answer (German)\n- Correction: ... (English)\n- Explanation: ... (English)\n- Next question (German)"
                    )
                else:
                    system_prompt = (
                        "You are Sir Felix, a strict but supportive Goethe B1 examiner. "
                        "ALWAYS correct and explain in ENGLISH only. "
                        "1. Answer the student's message in B1-level German (max 2–3 sentences). "
                        "2. If there are mistakes, show the corrected sentence(s) under 'Correction:' (in English). "
                        "3. Give a short grammar explanation (in English). "
                        "4. If the answer is perfect, say so and still give a tip in English. "
                        "5. End with a next question or prompt in German."
                        "Format your reply:\n"
                        "- Your answer (German)\n- Correction: ... (English)\n- Explanation: ... (English)\n- Next question (German)"
                    )
            conversation = [
                {"role": "system", "content": system_prompt},
                st.session_state["messages"][-1]
            ]
            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))
            st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
            st.experimental_rerun()  # Only here to refresh the form after AI answer

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
            st.session_state.update({
                "step": prev,
                "messages": [],
                "turn_count": 0,
                "custom_chat_level": None,
            })
    with col2:
        if session_ended and st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6


# ===============================
#         STAGE 6: SESSION SUMMARY & RESTART
# ===============================
def stage_6_summary():
    if st.session_state.get("step") != 6:
        return
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

# ===============================
#         STAGE 7: PRESENTATION PRACTICE (A2/B1) WITH STYLED CHAT
# ===============================
def stage_7_presentation():
    if st.session_state.get("step") != 7:
        return

    def presentation_keywords_input(safe_rerun):
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

    def generate_ai_reply_and_rerun():
        placeholder = st.empty()
        placeholder.info("🧑‍🏫 Sir Felix is typing...")

        if st.session_state.presentation_level == 'A2':
            kws = list(st.session_state.a2_keywords or [])
            topic = st.session_state.presentation_topic
            next_kw = next((kw for kw in kws if kw not in st.session_state.a2_keyword_progress), kws[0])
            system = (
                f"You are Sir Felix, an intelligent and friendly German A2 teacher. "
                f"You are helping a student practice for an upcoming German presentation. "
                f"Always keep the conversation focused on the topic '{topic}' and the keywords: {', '.join(kws)}. "
                f"Right now, focus especially on the keyword '{next_kw}'. "
                "You must always use only A2-level vocabulary and grammar in your questions, examples, and corrections. "
                "Whenever possible, include the current keyword in your question or model answer. "
                "ALWAYS give correction and explanation in ENGLISH. "
                "Ask questions that help them give better, fuller answers and practice what they'll say. "
                "Do not move to a new topic or keyword until the current one has been covered well. "
                "Act as both a helpful coach and a chat partner—encourage, teach, and help them improve for their real presentation!"
            )
        else:  # B1 logic
            topic = st.session_state.presentation_topic
            steps = [
                f"You are Sir Felix, a motivating B1 teacher. Only discuss the student topic: '{topic}'. Ask for the student's opinion in German. Give positive feedback in English. If you correct a sentence, explain the correction in English.",
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
        st.chat_message("assistant", avatar="🧑‍🏫").markdown(reply)
        st.session_state.presentation_messages.append({'role':'assistant','content':reply})
        safe_rerun()

    def presentation_chat_loop(generate_ai_reply_and_rerun, safe_rerun):
        if st.session_state.presentation_step != 3:
            return

        msgs = st.session_state.presentation_messages
        need_ai = (
            not msgs or
            (msgs and msgs[-1]['role'] == 'user' and (len(msgs) < 2 or msgs[-2]['role'] != 'assistant'))
        )
        if need_ai:
            generate_ai_reply_and_rerun()

        for m in st.session_state.presentation_messages:
            pnl = "👤" if m['role'] == 'user' else "🧑‍🏫"
            bubble = "background:#bee3f8;" if pnl == "🧑‍🏫" else "background:#f1f1f1;"
            name = "Sir Felix" if pnl == "🧑‍🏫" else "Student"
            st.markdown(
                f"<div style='margin:10px 0;padding:1em 1.2em;{bubble}border-radius:1em;max-width:65vw;min-width:110px;box-shadow:0 1px 4px #e5e5e5;'><b>{name}:</b><br>{m['content']}</div>",
                unsafe_allow_html=True
            )

        inp = st.chat_input("Type your response...")
        if inp:
            today = str(date.today())
            code = st.session_state.get("student_code", "(unknown)")
            key = f"{code}_{today}"
            st.session_state['daily_usage'][key] += 1
            st.session_state.presentation_messages.append({'role': 'user', 'content': inp})
            st.session_state.presentation_turn_count += 1
            if st.session_state.presentation_level == 'A2':
                for k in st.session_state.a2_keywords or []:
                    if k.lower() in inp.lower():
                        st.session_state.a2_keyword_progress.add(k)
            generate_ai_reply_and_rerun()

        max_turns = 12
        done = st.session_state.presentation_turn_count
        st.progress(min(done / max_turns, 1.0))
        st.markdown(f"**Progress:** Turn {done}/{max_turns}")
        st.markdown("---")

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

    if "presentation_step" not in st.session_state or st.session_state["presentation_step"] not in [0,1,2,3]:
        st.session_state["presentation_step"] = 0
        st.session_state["presentation_level"] = None
        st.session_state["presentation_topic"] = ""
        st.session_state["a2_keywords"] = None
        st.session_state["a2_keyword_progress"] = set()
        st.session_state["presentation_messages"] = []
        st.session_state["presentation_turn_count"] = 0

    today = str(date.today())
    code = st.session_state.get("student_code", "(unknown)")
    key = f"{code}_{today}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(key, 0)
    used = st.session_state["daily_usage"][key]
    st.info(f"Student code: `{code}` | Chats today: {used}/25")
    if used >= 25:
        st.warning("You’ve reached today’s limit of 25 chat turns. Please come back tomorrow.")
        return

    st.header("🎤 Presentation Practice (A2 & B1)")

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

    if st.session_state.presentation_step == 1:
        st.info("Please enter your presentation topic (English or German). 🔖")
        t = st.text_input("Topic:", key="topic_input")
        if st.button("Submit Topic") and t:
            st.session_state.presentation_topic = t
            st.session_state.presentation_messages.append({'role':'user','content':t})
            st.session_state.presentation_step = 2 if st.session_state.presentation_level == 'A2' else 3
            safe_rerun()
        return

    if st.session_state.presentation_level == "A2" and st.session_state.presentation_step == 2:
        presentation_keywords_input(safe_rerun)
        return

    if st.session_state.presentation_step == 3:
        presentation_chat_loop(generate_ai_reply_and_rerun, safe_rerun)
        return

# ===============================
#         MAIN APP
# ===============================
setup_ui_and_state()
stage_3_login_and_mode()
stage_4_exam_part()
stage_5_chat()
stage_6_summary()
stage_7_presentation()
