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

# ---- Session state init ----
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

# ---- Prompt Engineering ----
def get_ai_system_prompt(mode, level, teil, topic, custom_intro_done):
    # ---- Exam Mode Prompts ----
    if mode == "Geführte Prüfungssimulation (Exam Mode)":
        if level == "A2":
            return (
                f"You are Herr Felix, a strict but friendly Goethe A2 examiner. "
                f"Stay strictly on the topic: {topic}. "
                "Correct and give a grammar tip ONLY for the student's most recent answer. "
                "1. Answer in very simple A2-level German (max 2–3 sentences). "
                "2. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                "3. Give a short grammar tip (in English, one short sentence). "
                "4. If the answer is perfect, say so and still give a tip in English. "
                "5. End with a next question in German, always about the same topic. "
                "Format your reply:\n"
                "- Your answer (German)\n- Correction: ...\n- Grammar Tip: ...\n- Next question (German, about the same topic)"
            )
        elif level == "B1":
            if teil and "Teil 3" in teil:
                return (
                    f"You are Herr Felix, the examiner in a German B1 oral exam (Teil 3: Feedback & Questions). "
                    f"Stay strictly on the topic: {topic}. "
                    "The student is supposed to ask you one valid question about their presentation. "
                    "1. Read the student's message. "
                    "2. Confirm if they wrote exactly one question—praise or politely correct. "
                    "3. If valid, answer briefly in simple German. "
                    "4. End with clear exam tips in English."
                )
            else:
                return (
                    f"You are Herr Felix, a strict but supportive Goethe B1 examiner. "
                    f"Stay strictly on the topic: {topic}. "
                    "Correct and give a grammar tip ONLY for the student's most recent answer. "
                    "1. Answer in B1-level German (max 2–3 sentences). "
                    "2. If there are mistakes, show the corrected sentence(s) under 'Correction:'. "
                    "3. Give a short grammar tip (in English, one short sentence). "
                    "4. If the answer is perfect, say so and still give a tip in English. "
                    "5. End with a next question or prompt in German, always about the same topic. "
                    "Format your reply:\n"
                    "- Your answer (German)\n- Correction: ...\n- Grammar Tip: ...\n- Next question (German, about the same topic)"
                )
    # ---- Custom Topic Prompts ----
    elif mode == "Eigenes Thema/Frage (Custom Topic Chat)":
        if level == "A2":
            return (
                f"You are Herr Felix, a creative but strict A2 German teacher and exam trainer. "
                f"The student has just provided their presentation topic: {topic}. "
                "1. Provide practical ideas/examples in English on how an A2 student can organize a presentation about this topic. "
                "2. Suggest four relevant keywords from the topic as main points. "
                "3. Ask the student one clear question in German, using those keywords and practical ideas (3–7 sentences). "
                "Only output the three numbered items. Do NOT include emojis, role tags, or extra headings."
            )
        elif level == "B1":
            if not custom_intro_done:
                return (
                    f"You are Herr Felix, a supportive B1 German teacher and exam trainer. "
                    f"The student has just given you their presentation topic: {topic}. "
                    "1. First, give a few practical ideas/examples (in German) on how a B1 student can build a presentation about this topic. "
                    "2. Suggest possible points: Meinung (opinion), Vorteil (advantage), Nachteil (disadvantage), Situation im Heimatland (situation in home country), etc. "
                    "3. Then ask the student ONE question about their opinion (Meinung) on the topic (in German). "
                    "Give corrections and a grammar tip if needed. "
                    "Never repeat this ideas/tips message again in this chat session."
                )
            else:
                return (
                    f"You are Herr Felix, a supportive B1 German teacher and exam trainer. "
                    f"Stay strictly on the topic: {topic}. "
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
    # Default fallback
    return f"You are Herr Felix, answer as a German teacher/examiner for {level}."

# ---- AI Chat Utility ----
def chat_with_openai(system_prompt, message_history):
    # Uncomment and adapt for production
    # client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
    # messages = [{"role": "system", "content": system_prompt}] + message_history
    # try:
    #     resp = client.chat.completions.create(
    #         model="gpt-4o", messages=messages
    #     )
    #     return resp.choices[0].message.content
    # except Exception as e:
    #     return "Sorry, there was a problem generating a response."
    # DEMO: Fake AI reply
    return "Dies ist eine Beispielantwort von Herr Felix."

def get_recent_message_history(messages, N=6):
    return messages[-N:] if len(messages) > N else messages

# ---- Step Functions ----

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
        prompt = f"Practice: {selected_topic}"
        st.session_state["initial_prompt"] = prompt
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["step"] = 5

def step_5_chat():
    st.markdown("### 💬 Chat with Herr Felix")
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(msg['content'])
        else:
            with st.chat_message("user"):
                st.markdown(msg['content'])
    typed = st.chat_input("💬 Type your answer here...", key="stage5_typed_input")
    if typed:
        st.session_state["messages"].append({"role": "user", "content": typed})
        # --- AI logic with real prompt ---
        mode = st.session_state.get("selected_mode", "")
        level = st.session_state.get("selected_exam_level") or st.session_state.get("custom_chat_level")
        teil = st.session_state.get("selected_teil")
        # For custom mode, you could allow user to type their own topic
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
