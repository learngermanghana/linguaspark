import os
import random
from datetime import date
import streamlit as st
from openai import OpenAI

# --------- SESSION STATE SETUP ----------
def init_session():
    defaults = {
        "step": 1,
        "student_code": "",
        "daily_usage": {},
        "messages": [],
        "turn_count": 0,
        "custom_chat_level": None,
        "custom_topic_intro_done": False,
        "current_b1_teil3_topic": "",
        "selected_mode": None,
        "selected_exam_level": None,
        "selected_teil": None,
        "initial_prompt": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
init_session()

# --------- PAGE CONFIG & HEADER ----------
st.set_page_config(page_title="Falowen – Your AI Conversation Partner", layout="centered")
st.markdown("""
    <div style='display:flex;align-items:center;gap:18px;margin-bottom:22px;'>
        <img src='https://cdn-icons-png.flaticon.com/512/6815/6815043.png' width='54' style='border-radius:50%;border:2.5px solid #51a8d2;box-shadow:0 2px 8px #cbe7fb;'/>
        <div>
            <span style='font-size:2.1rem;font-weight:bold;color:#17617a;letter-spacing:2px;'>Falowen</span><br>
            <span style='font-size:1.08rem;color:#268049;'>Your personal German speaking coach (Herr Felix)</span>
        </div>
    </div>
    """, unsafe_allow_html=True
)

# --------- DATA: EXAM PARTS & TOPICS ---------
A2_PARTS = [
    "Teil 1 – Fragen zu Schlüsselwörtern",
    "Teil 2 – Bildbeschreibung & Diskussion",
    "Teil 3 – Gemeinsam planen"
]
B1_PARTS = [
    "Teil 1 – Gemeinsam planen (Dialogue)",
    "Teil 2 – Präsentation (Monologue)",
    "Teil 3 – Feedback & Fragen stellen"
]
A2_TOPICS = {
    A2_PARTS[0]: [
        "Wohnort", "Tagesablauf", "Freizeit", "Sprachen", "Essen & Trinken", "Haustiere",
        "Lieblingsmonat", "Jahreszeit", "Sport", "Kleidung (Sommer)", "Familie", "Beruf",
        "Hobbys", "Feiertage", "Reisen", "Lieblingsessen", "Schule", "Wetter",
        "Auto oder Fahrrad", "Perfekter Tag"
    ],
    A2_PARTS[1]: [
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
    ],
    A2_PARTS[2]: [
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
}
B1_TOPICS = {
    B1_PARTS[0]: [
        "Mithilfe beim Sommerfest", "Eine Reise nach Köln planen",
        "Überraschungsparty organisieren", "Kulturelles Ereignis (Konzert, Ausstellung) planen",
        "Museumsbesuch organisieren"
    ],
    B1_PARTS[1]: [
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
    ],
    B1_PARTS[2]: [
        "Fragen stellen zu einer Präsentation", "Positives Feedback geben",
        "Etwas überraschend finden oder planen", "Weitere Details erfragen"
    ]
}

# --------- PROMPT ENGINEERING ---------
def get_ai_system_prompt(mode, level, teil, topic, custom_intro_done):
    if mode == "Geführte Prüfungssimulation (Exam Mode)":
        if level == "A2":
            return (
                "You are Herr Felix, a strict but friendly Goethe A2 examiner. "
                "Stay strictly on the student's selected topic but use different keywords in every three to four messages. "
                "Correct and give a grammar tip ONLY for the student's most recent answer, not for your own or earlier messages. "
                "1. Ask students to give you some keywords to guide the conversation. Give them examples based on the topic. "
                "2. Answer the student's message in very simple A2-level German (max 2–3 sentences). "
                "3. Help students with ideas on how to express themselves on the chosen topic (max 2–3 sentences). "
                "4. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                "5. Give a short grammar tip (in English, one short sentence). "
                "6. If the answer is perfect, say so and still give a tip in English. "
                "7. End with a next question or prompt in German, always about the same topic. "
                "Format your reply:\n"
                "- Your answer (German)\n- Correction: ...\n- Grammar Tip: ...\n- Next question (German, about the same topic)"
            )
        elif level == "B1":
            if teil and "Teil 3" in teil:
                return (
                    "You are Herr Felix, the examiner in a German B1 oral exam (Teil 3: Feedback & Questions). "
                    f"**IMPORTANT: Stay strictly on the topic:** {topic}. "
                    "Never change the topic. The student is supposed to ask you one valid question about their presentation. "
                    "1. Read the student's message. "
                    "2. Confirm if they wrote exactly one question—praise or politely correct. "
                    "3. If valid, answer briefly in simple German. "
                    "4. End with clear exam tips in English."
                )
            else:
                return (
                    "You are Herr Felix, a strict but supportive Goethe B1 examiner. "
                    "Stay strictly on the student's selected topic in every message. "
                    "Correct and give a grammar tip ONLY for the student's most recent answer, not for your own or earlier messages. "
                    "1. Answer the student's message in B1-level German (max 2–3 sentences). "
                    "2. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                    "3. Give a short grammar tip (in English, one short sentence). "
                    "4. If the answer is perfect, say so and still give a tip in English. "
                    "5. End with a next question or prompt in German, always about the same topic. "
                    "Format your reply:\n"
                    "- Your answer (German)\n- Correction: ...\n- Grammar Tip: ...\n- Next question (German, about the same topic)"
                )
    elif mode == "Eigenes Thema/Frage (Custom Topic Chat)":
        if level == "A2":
            return (
                "You are Herr Felix, a creative but strict A2 German teacher and exam trainer.\n"
                "The student has just provided their presentation topic.\n"
                "1. Provide practical ideas/examples in English on how an A2 student can organize a presentation about this topic.\n"
                "2. Suggest four relevant keywords from the topic as main points.\n"
                "3. Ask the student one clear question in German, using those keywords and practical ideas (3–7 sentences).\n"
                "Only output the three numbered items. Do NOT include emojis, role tags, or extra headings."
            )
        elif level == "B1":
            if not custom_intro_done:
                return (
                    "You are Herr Felix, a supportive B1 German teacher and exam trainer. "
                    "The student has just given you their presentation topic. "
                    "1. First, give a few practical ideas/examples (in German) on how a B1 student can build a presentation about this topic. "
                    "2. Suggest possible points: Meinung (opinion), Vorteil (advantage), Nachteil (disadvantage), Situation im Heimatland (situation in home country), etc. "
                    "3. Then ask the student ONE question about their opinion (Meinung) on the topic (in German). "
                    "Give corrections and a grammar tip if needed. "
                    "Never repeat this ideas/tips message again in this chat session."
                )
            else:
                return (
                    "You are Herr Felix, a supportive B1 German teacher and exam trainer. "
                    "Reply at B1-level in German. "
                    "Always stay strictly on the student's current topic in every reply. "
                    "Ask NO MORE THAN ONE question at a time—never ask two or more questions in one reply. "
                    "Ask the student about their opinion, or about one advantage, one disadvantage, or situation in their home country—but one at a time, rotating each turn. "
                    "Correct and give a grammar tip for the student's last answer (always in English). "
                    "Your reply format:\n"
                    "- Your answer (German)\n"
                    "- Correction (if needed, in German)\n"
                    "- Grammar Tip (in English, one short sentence)\n"
                    "- Next question (in German, about the same topic, and only ONE question)\n"
                    "Never repeat the general topic ideas again."
                )
    return "You are Herr Felix. Answer as a German language examiner."

# --------- OPENAI CHAT CALLS + CONTEXT WINDOW ---------
def get_recent_message_history(messages, N=6):
    """Return the last N exchanges for context (user+assistant pairs)."""
    return messages[-N:] if len(messages) > N else messages

def chat_with_openai(system_prompt, message_history, api_key, model="gpt-4o", fallback_model="gpt-3.5-turbo"):
    client = OpenAI(api_key=api_key)
    messages = [{"role": "system", "content": system_prompt}] + message_history
    try:
        resp = client.chat.completions.create(
            model=model, messages=messages
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.warning(f"GPT-4o failed: {e} - retrying with {fallback_model}")
        try:
            resp = client.chat.completions.create(
                model=fallback_model, messages=messages
            )
            return resp.choices[0].message.content
        except Exception as e2:
            st.error(f"All models failed: {e2}")
            return "Sorry, there was a problem generating a response."

# --------- UI FLOW (STEPS) ---------
if st.session_state["step"] == 1:
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️", key="stage1_next"):
        code_clean = code.strip().lower()
        # (Add your code verification here!)
        st.session_state["student_code"] = code_clean
        st.session_state["step"] = 2
        st.experimental_rerun()

elif st.session_state["step"] == 2:
    st.success("Welcome to Falowen!")
    st.info("This is your training space for A2/B1 Goethe exams. You'll practice with real exam tasks and receive instant feedback!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage2_back"):
            st.session_state["step"] = 1
            st.experimental_rerun()
    with col2:
        if st.button("Next ➡️", key="stage2_next"):
            st.session_state["step"] = 3
            st.experimental_rerun()

elif st.session_state["step"] == 3:
    st.header("Wie möchtest du üben? (How would you like to practice?)")
    mode = st.radio(
        "Choose your practice mode:",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)"],
        index=0,
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage3_back"):
            st.session_state["step"] = 2
            st.experimental_rerun()
    with col2:
        if st.button("Next ➡️", key="stage3_next"):
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["step"] = 4 if mode == "Geführte Prüfungssimulation (Exam Mode)" else 5
            st.experimental_rerun()

elif st.session_state["step"] == 4:
    st.markdown("### 📝 Prüfungsteil wählen / Choose exam part")
    st.info("Select your **exam level**, **part**, and **topic** to practice. You can always go back or switch parts later.")

    exam_level = st.radio(
        "🔍 Prüfungsniveau / Exam Level:",
        ["A2", "B1"],
        horizontal=True,
        index=0 if st.session_state.get("selected_exam_level", "A2") == "A2" else 1,
        key="exam_level_select"
    )
    st.session_state["selected_exam_level"] = exam_level
    part_options = A2_PARTS if exam_level == "A2" else B1_PARTS
    topics_dict = A2_TOPICS if exam_level == "A2" else B1_TOPICS

    teil = st.selectbox(
        "🧩 Welchen Teil möchtest du üben? / Which part do you want to practice?",
        part_options,
        key="exam_teil_select"
    )
    st.session_state["selected_teil"] = teil
    current_topics = topics_dict[teil]
    default_topic = random.choice(current_topics)
    selected_topic = st.selectbox(
        "📚 Thema wählen / Choose a topic:",
        current_topics,
        index=current_topics.index(default_topic),
        key="topic_select"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage4_back"):
            st.session_state["step"] = 3
            st.experimental_rerun()
    with col2:
        if st.button("Start Chat ➡️", key="stage4_start"):
            # --- Use selected topic for initial prompt ---
            if exam_level == "A2":
                if teil.startswith("Teil 1"):
                    prompt = f"**A2 Teil 1:** The Keyword is **{selected_topic}**. Stelle eine passende Frage und beantworte eine Frage dazu. Beispiel: 'Hast du Geschwister? – Ja, ich habe eine Schwester.'"
                elif teil.startswith("Teil 2"):
                    prompt = f"**A2 Teil 2:** Talk about the topic: **{selected_topic}**."
                else:
                    prompt = f"**A2 Teil 3:** Plan a meeting with Herr Felix: **{selected_topic}**. Mache Vorschläge, reagiere, und trefft eine Entscheidung."
            else:
                if teil.startswith("Teil 1"):
                    prompt = f"**B1 Teil 1:** Plant gemeinsam: **{selected_topic}**. Mache Vorschläge, reagiere auf deinen Partner, und trefft eine Entscheidung."
                elif teil.startswith("Teil 2"):
                    prompt = f"**B1 Teil 2:** Halte eine Präsentation über das Thema: **{selected_topic}**. Begrüße, nenne das Thema, gib deine Meinung, teile Vor- und Nachteile, fasse zusammen."
                else:
                    prompt = f"**B1 Teil 3:** {selected_topic}: Dein Partner hat eine Präsentation gehalten. Stelle 1–2 Fragen dazu und gib positives Feedback."
            st.session_state["initial_prompt"] = prompt
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["step"] = 5
            st.experimental_rerun()

elif st.session_state["step"] == 5:
    st.info(
        f"Student code: `{st.session_state['student_code']}` | "
        f"Today's practice: {st.session_state['daily_usage'].get(st.session_state['student_code'],0)}/25"
    )
    # Show chat history
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"🧑‍🏫 Herr Felix: {msg['content']}")
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")
    # Chat input always visible
    typed = st.chat_input("💬 Oder tippe deine Antwort hier...", key="stage5_typed_input")
    if typed:
        st.session_state["messages"].append({"role": "user", "content": typed})
        mode = st.session_state.get("selected_mode", "")
        level = st.session_state.get("selected_exam_level") or st.session_state.get("custom_chat_level")
        teil = st.session_state.get("selected_teil")
        topic = st.session_state.get("current_b1_teil3_topic") or st.session_state.get("initial_prompt", "")
        custom_intro_done = st.session_state.get("custom_topic_intro_done", False)
        system_prompt = get_ai_system_prompt(mode, level, teil, topic, custom_intro_done)
        message_history = get_recent_message_history(st.session_state["messages"], N=6)
        ai_reply = chat_with_openai(
            system_prompt,
            message_history,
            api_key=st.secrets["general"]["OPENAI_API_KEY"]
        )
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
        st.experimental_rerun()
        return
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
            st.session_state.update({
                "step": prev,
                "messages": [],
                "turn_count": 0,
                "custom_chat_level": None,
                "custom_topic_intro_done": False,
            })
            st.experimental_rerun()
    with col2:
        if st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6
            st.experimental_rerun()

elif st.session_state["step"] == 6:
    st.success("Session complete! 🎉")
    # Show a summary: answers, corrections, stats (expand as needed)
    if st.button("Restart", key="summary_restart"):
        st.session_state["step"] = 1
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["custom_chat_level"] = None
        st.session_state["custom_topic_intro_done"] = False
        st.experimental_rerun()
