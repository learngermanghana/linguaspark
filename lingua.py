import os
import random
from datetime import date
import streamlit as st
from openai import OpenAI

# ---- Session State ----
def init_session():
    defaults = {
        "step": 1,
        "student_code": "",
        "messages": [],
        "turn_count": 0,
        "selected_mode": None,
        "selected_exam_level": None,
        "selected_teil": None,
        "initial_prompt": None,
        "custom_chat_level": None,
        "custom_topic_intro_done": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
init_session()

# ---- Data ----
A2_PARTS = [
    "Teil 1 – Fragen zu Schlüsselwörtern",
    "Teil 2 – Bildbeschreibung & Diskussion",
    "Teil 3 – Gemeinsam planen"
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
B1_PARTS = [
    "Teil 1 – Gemeinsam planen (Dialogue)",
    "Teil 2 – Präsentation (Monologue)",
    "Teil 3 – Feedback & Fragen stellen"
]
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

# ---- Prompt Engineering ----
def get_ai_system_prompt(mode, level, teil, topic, custom_intro_done):
    # Put all your advanced prompt logic here as discussed above!
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

# ---- Chat Utilities ----
def get_recent_message_history(messages, N=6):
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

# ---- Step 1: Login ----
def step_1_login():
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️", key="stage1_next"):
        st.session_state["student_code"] = code.strip().lower()
        st.session_state["step"] = 2
        st.experimental_rerun()
        return

# ---- Step 2: Welcome ----
def step_2_welcome():
    st.success("Welcome to Falowen!")
    if st.button("Next ➡️", key="stage2_next"):
        st.session_state["step"] = 3
        st.experimental_rerun()
        return

# ---- Step 3: Mode Selection ----
def step_3_mode():
    mode = st.radio(
        "Choose your practice mode:",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)"],
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode
    if st.button("Next ➡️", key="stage3_next"):
        st.session_state["step"] = 4 if mode == "Geführte Prüfungssimulation (Exam Mode)" else 5
        st.experimental_rerun()
        return

# ---- Step 4: Exam Part & Topic ----
def step_4_exam_part():
    st.markdown("### 📝 Prüfungsteil wählen / Choose exam part")
    exam_level = st.radio("Exam Level:", ["A2", "B1"], key="exam_level_select")
    st.session_state["selected_exam_level"] = exam_level
    part_options = A2_PARTS if exam_level == "A2" else B1_PARTS
    topics_dict = A2_TOPICS if exam_level == "A2" else B1_TOPICS

    teil = st.selectbox("Part to practice:", part_options, key="exam_teil_select")
    st.session_state["selected_teil"] = teil
    current_topics = topics_dict[teil]
    selected_topic = st.selectbox("Choose a topic:", current_topics, key="topic_select")

    if st.button("Start Chat ➡️", key="stage4_start"):
        # Set prompt based on level/teil/topic (see your real logic for detailed messages)
        prompt = f"Practice: {selected_topic}"
        st.session_state["initial_prompt"] = prompt
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["step"] = 5
        st.experimental_rerun()
        return

# ---- Step 5: Chat ----
def step_5_chat():
    st.markdown("### 💬 Chat with Herr Felix")
    # Show chat bubbles, user on right, AI on left
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(msg['content'])
        else:
            with st.chat_message("user"):
                st.markdown(msg['content'])
    # Chat input always visible
    typed = st.chat_input("💬 Type your answer here...", key="stage5_typed_input")
    if typed:
        st.session_state["messages"].append({"role": "user", "content": typed})
        mode = st.session_state.get("selected_mode", "")
        level = st.session_state.get("selected_exam_level") or st.session_state.get("custom_chat_level")
        teil = st.session_state.get("selected_teil")
        topic = st.session_state.get("initial_prompt", "")
        custom_intro_done = st.session_state.get("custom_topic_intro_done", False)
        system_prompt = get_ai_system_prompt(mode, level, teil, topic, custom_intro_done)
        message_history = get_recent_message_history(st.session_state["messages"], N=6)
        ai_reply = chat_with_openai(system_prompt, message_history, api_key=st.secrets["general"]["OPENAI_API_KEY"])
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
        st.experimental_rerun()
        return
    if st.button("Summary / Restart"):
        st.session_state["step"] = 6
        st.experimental_rerun()
        return

# ---- Step 6: Summary ----
def step_6_summary():
    st.success("Session complete! 🎉")
    # Expand: Show message history, corrections, feedback, download, etc.
    if st.button("Restart", key="summary_restart"):
        st.session_state["step"] = 1
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["custom_chat_level"] = None
        st.session_state["custom_topic_intro_done"] = False
        st.experimental_rerun()
        return

# ---- Dispatcher ----
step = st.session_state["step"]
if step == 1:
    step_1_login()
elif step == 2:
    step_2_welcome()
elif step == 3:
    step_3_mode()
elif step == 4:
    step_4_exam_part()
elif step == 5:
    step_5_chat()
elif step == 6:
    step_6_summary()
