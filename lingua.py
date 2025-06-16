import streamlit as st
import random
from datetime import date
# from openai import OpenAI

# ---- Exam Data ----
A2_PARTS = [
    "Teil 1 – Fragen zu Schlüsselwörtern",
    "Teil 2 – Bildbeschreibung & Diskussion",
    "Teil 3 – Gemeinsam planen"
]
A2_TOPICS = {
    A2_PARTS[0]: ["Wohnort", "Tagesablauf", "Freizeit"],
    A2_PARTS[1]: ["Was machen Sie am Wochenende?"],
    A2_PARTS[2]: ["Zusammen ins Kino gehen"]
}
B1_PARTS = [
    "Teil 1 – Gemeinsam planen (Dialogue)",
    "Teil 2 – Präsentation (Monologue)",
    "Teil 3 – Feedback & Fragen stellen"
]
B1_TOPICS = {
    B1_PARTS[0]: ["Mithilfe beim Sommerfest"],
    B1_PARTS[1]: ["Ausbildung"],
    B1_PARTS[2]: ["Fragen stellen zu einer Präsentation"]
}

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
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_session()

def get_ai_system_prompt(mode, level, teil, topic, custom_intro_done):
    if mode == "Geführte Prüfungssimulation (Exam Mode)":
        if level == "A2":
            return (
                f"You are Herr Felix, a strict but friendly Goethe A2 examiner. "
                f"Stay strictly on the topic: {topic}. "
                "Correct and give a grammar tip ONLY for the student's most recent answer. "
                "Format your reply as follows:\n"
                "- Your answer (German)\n"
                "- Correction: ...\n"
                "- Grammar Tip: ...\n"
                "- Next question (German, about the same topic)"
            )
        elif level == "B1":
            return (
                f"You are Herr Felix, a strict but supportive Goethe B1 examiner. "
                f"Stay strictly on the topic: {topic}. "
                "Correct and give a grammar tip ONLY for the student's most recent answer. "
                "Format your reply as follows:\n"
                "- Your answer (German)\n"
                "- Correction: ...\n"
                "- Grammar Tip: ...\n"
                "- Next question (German, about the same topic)"
            )
    elif mode == "Eigenes Thema/Frage (Custom Topic Chat)":
        if level == "A2":
            return (
                f"You are Herr Felix, a creative but strict A2 German teacher and exam trainer. "
                f"The student has just provided their presentation topic: {topic}. "
                "1. Provide practical ideas/examples in English on how an A2 student can organize a presentation about this topic. "
                "2. Suggest four relevant keywords from the topic as main points. "
                "3. Ask the student one clear question in German, using those keywords and practical ideas (3–7 sentences). "
                "Format your reply as follows:\n"
                "- Your answer (German)\n"
                "- Correction: ...\n"
                "- Grammar Tip: ...\n"
                "- Next question (German, about the same topic)"
            )
        elif level == "B1":
            if not custom_intro_done:
                return (
                    f"You are Herr Felix, a supportive B1 German teacher and exam trainer. "
                    f"The student has just given you their presentation topic: {topic}. "
                    "1. Give practical ideas/examples in German for a B1 presentation about this topic. "
                    "2. Suggest points: Meinung, Vorteil, Nachteil, Situation im Heimatland. "
                    "3. Ask one question about their opinion on the topic in German. "
                    "Format your reply as follows:\n"
                    "- Your answer (German)\n"
                    "- Correction: ...\n"
                    "- Grammar Tip: ...\n"
                    "- Next question (German, about the same topic)"
                )
            else:
                return (
                    f"You are Herr Felix, a supportive B1 German teacher and exam trainer. "
                    f"Stay strictly on the topic: {topic}. "
                    "Reply at B1-level in German. "
                    "Always stay strictly on the student's current topic in every reply. "
                    "Correct and give a grammar tip for the student's last answer (always in English). "
                    "Format your reply as follows:\n"
                    "- Your answer (German)\n"
                    "- Correction: ...\n"
                    "- Grammar Tip: ...\n"
                    "- Next question (German, about the same topic, and only ONE question)"
                )
    return f"You are Herr Felix, answer as a German teacher/examiner for {level}."

def chat_with_openai(system_prompt, message_history):
    # Uncomment & replace for real API use
    # client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
    # messages = [{"role": "system", "content": system_prompt}] + message_history
    # try:
    #     resp = client.chat.completions.create(
    #         model="gpt-4o", messages=messages
    #     )
    #     return resp.choices[0].message.content
    # except Exception as e:
    #     return "Sorry, there was a problem generating a response."
    # Demo reply:
    # The format here should match your AI output format for real use.
    return (
        "Guten Morgen! Ich stehe jeden Tag um 7 Uhr auf. Dann frühstücke ich.\n"
        "Correction: Ich stehe jeden Tag um 7 Uhr **auf** (verb at the end).\n"
        "Grammar Tip: In separable verbs, the prefix goes to the end.\n"
        "Next question: Was machst du nach dem Frühstück?"
    )

def get_recent_message_history(messages, N=6):
    return messages[-N:] if len(messages) > N else messages

def show_formatted_ai_reply(ai_reply):
    """
    Splits the AI reply into sections and displays each part with a different style.
    Expected sections: Correction, Grammar Tip, Next Question.
    """
    # Parse out the sections
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

    st.markdown(f"**📝 Answer:**  \n{main.strip()}", unsafe_allow_html=True)
    if correction.strip():
        st.markdown(f"<div style='color:#c62828'><b>✏️ Correction:</b>  \n{correction.strip()}</div>", unsafe_allow_html=True)
    if grammatik.strip():
        st.markdown(f"<div style='color:#1565c0'><b>📚 Grammar Tip:</b>  \n{grammatik.strip()}</div>", unsafe_allow_html=True)
    if followup.strip():
        st.markdown(f"<div style='color:#388e3c'><b>➡️ Next question:</b>  \n{followup.strip()}</div>", unsafe_allow_html=True)

def step_1_login():
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️", key="stage1_next"):
        st.session_state["student_code"] = code.strip().lower()
        st.session_state["step"] = 2

def step_2_welcome():
    st.success("Welcome to Falowen!")
    if st.button("Next ➡️", key="stage2_next"):
        st.session_state["step"] = 3

def step_3_mode():
    mode = st.radio(
        "Choose your practice mode:",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)"],
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode
    if st.button("Next ➡️", key="stage3_next"):
        st.session_state["step"] = 4 if mode == "Geführte Prüfungssimulation (Exam Mode)" else 5

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
        st.session_state["initial_prompt"] = selected_topic
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["step"] = 5

def step_5_chat():
    st.header("💬 Chat mit Herr Felix")
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                show_formatted_ai_reply(msg["content"])
        else:
            with st.chat_message("user"):
                st.markdown(msg["content"])
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
        ai_reply = chat_with_openai(system_prompt, message_history)
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
    if st.button("Summary / Restart"):
        st.session_state["step"] = 6

def step_6_summary():
    st.success("Session complete! 🎉")
    if st.button("Restart", key="summary_restart"):
        st.session_state["step"] = 1
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["custom_chat_level"] = None
        st.session_state["custom_topic_intro_done"] = False

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
