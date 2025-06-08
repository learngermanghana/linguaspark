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

def load_codes():
    if os.path.exists(CODES_FILE):
        df = pd.read_csv(CODES_FILE)
        if "code" not in df.columns:
            df = pd.DataFrame(columns=["code"])
        df["code"] = df["code"].astype(str).str.strip().str.lower()
    else:
        df = pd.DataFrame(columns=["code"])
    return df

if "step" not in st.session_state:
    st.session_state["step"] = 1

if "student_code" not in st.session_state:
    st.session_state["student_code"] = ""

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
if st.session_state["step"] == 2:
    # Fun fact list (add/remove as you wish)
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
    random_fact = random.choice(fun_facts)
    st.success(f"**Did you know?** {random_fact}")

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


if st.session_state["step"] == 3:
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
        custom_topic = st.text_input(
            "Type your own topic or question here (e.g. from Google Classroom, homework, or any free conversation)...",
            value=st.session_state.get("custom_topic", ""),
            key="custom_topic_input"
        )
        st.session_state["custom_topic"] = custom_topic

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage3_back"):
            st.session_state["step"] = 2
    with col2:
        if st.button("Next ➡️", key="stage3_next"):
            # Reset conversation state
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            # Decide next step
            if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                st.session_state["step"] = 5
            else:
                st.session_state["step"] = 4

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
    "Etwas überraschend finden", "Weitere Details erfragen"
]

if st.session_state["step"] == 4:
    st.header("Prüfungsteil wählen / Choose exam part")

    # 1) Exam level selector
    exam_level = st.selectbox(
        "Welches Prüfungsniveau möchtest du üben?",
        ["A2", "B1"],
        key="exam_level_select",
        index=0
    )
    st.session_state["selected_exam_level"] = exam_level

    # 2) Teil options based on level
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

    # 3) Teil selector
    teil = st.selectbox(
        "Welchen Teil möchtest du üben?",
        teil_options,
        key="exam_teil_select"
    )
    st.session_state["selected_teil"] = teil

    # 4) Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage4_back"):
            st.session_state["step"] = 3
    with col2:
        if st.button("Start Chat ➡️", key="stage4_start"):
            # Build the initial prompt based on the selections
            if exam_level == "A2":
                if teil.startswith("Teil 1"):
                    topic = random.choice(A2_TEIL1)
                    prompt = (
                        f"**A2 Teil 1:** Das Schlüsselwort ist **{topic}**. "
                        "Stelle eine passende Frage und beantworte eine Frage dazu. "
                        "Beispiel: 'Hast du Geschwister? – Ja, ich habe eine Schwester.'"
                    )
                elif teil.startswith("Teil 2"):
                    topic = random.choice(A2_TEIL2)
                    prompt = f"**A2 Teil 2:** Beschreibe oder diskutiere zum Thema: **{topic}**."
                else:
                    topic = random.choice(A2_TEIL3)
                    prompt = (
                        f"**A2 Teil 3:** Plant gemeinsam: **{topic}**. "
                        "Mache Vorschläge, reagiere, und trefft eine Entscheidung."
                    )
            else:  # B1
                if teil.startswith("Teil 1"):
                    topic = random.choice(B1_TEIL1)
                    prompt = (
                        f"**B1 Teil 1:** Plant gemeinsam: **{topic}**. "
                        "Mache Vorschläge, reagiere auf deinen Partner, und trefft eine Entscheidung."
                    )
                elif teil.startswith("Teil 2"):
                    topic = random.choice(B1_TEIL2)
                    prompt = (
                        f"**B1 Teil 2:** Halte eine Präsentation über das Thema: **{topic}**. "
                        "Begrüße, nenne das Thema, gib deine Meinung, teile Vor- und Nachteile, fasse zusammen."
                    )
                else:
                    topic = random.choice(B1_TEIL3)
                    prompt = (
                        f"**B1 Teil 3:** {topic}: Dein Partner hat eine Präsentation gehalten. "
                        "Stelle 1–2 Fragen dazu und gib positives Feedback."
                    )

            # Store and proceed
            st.session_state["initial_prompt"] = prompt
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["step"] = 5



    session_ended = st.session_state["turn_count"] >= max_turns
    used_today = st.session_state["daily_usage"][usage_key]

    rerun_needed = False
    if user_input and not session_ended:
        if used_today >= DAILY_LIMIT:
            st.warning("You’ve reached today’s free practice limit. Please come back tomorrow or contact your tutor for unlimited access!")
        else:
            st.session_state['messages'].append({'role': 'user', 'content': user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1
            rerun_needed = True

    # --- Display chat history ---
    for msg in st.session_state['messages']:
        if msg['role'] == 'assistant':
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Herr Felix:</span> {msg['content']}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- AI response & audio playback ---
    if rerun_needed and not session_ended and used_today < DAILY_LIMIT:
        try:
            extra_end = (
                "After 6 student answers, give a short, positive summary, "
                "suggest a new topic or a break, and do NOT answer further unless restarted."
                if st.session_state["turn_count"] >= max_turns else ""
            )
            # Prompt depends on mode
            if st.session_state.get("selected_mode") == "Eigenes Thema/Frage (Custom Topic Chat)":
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
                exam_level = st.session_state.get("selected_exam_level", "A2")
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
        st.session_state['ai_audio'] = ai_reply
        st.experimental_rerun()

    # --- Play audio for latest AI message, if available ---
    if "ai_audio" in st.session_state:
        try:
            tts = gTTS(st.session_state["ai_audio"], lang="de")
            tts_bytes = io.BytesIO()
            tts.write_to_fp(tts_bytes)
            tts_bytes.seek(0)
            tts_data = tts_bytes.read()
            st.audio(tts_data, format="audio/mp3")
        except Exception:
            st.info("Audio feedback not available or an error occurred.")

    if session_ended:
        st.success("🎉 **Session beendet!** Du hast fleißig geübt. Willst du ein neues Thema oder eine Pause?")
        if st.button("Next ➡️ (Summary/Restart)"):
            st.session_state["step"] = 6

    if st.button("⬅️ Back to previous step"):
        st.session_state["step"] = 4 if st.session_state.get("selected_mode") == "Geführte Prüfungssimulation (Exam Mode)" else 3
        st.session_state["messages"] = []
        st.session_state["corrections"] = []
        st.session_state["turn_count"] = 0
if st.session_state["step"] == 6:
    st.title("🎉 Congratulations!")
    st.markdown(
        "<h3 style='color:#33691e;'>Session completed!</h3>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"**You completed {st.session_state['turn_count']} conversation turns today.**<br>"
        "Would you like to start a new session or review another topic?",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Start New Session"):
            st.session_state["messages"] = []
            st.session_state["corrections"] = []
            st.session_state["turn_count"] = 0
            st.session_state["step"] = 1
            st.session_state["custom_topic"] = ""
    with col2:
        if st.button("⬅️ Back to Mode Selection"):
            st.session_state["messages"] = []
            st.session_state["corrections"] = []
            st.session_state["turn_count"] = 0
            st.session_state["step"] = 3
