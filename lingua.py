import random
import streamlit as st

# ---- (Optional) OpenAI import/setup ----
# from openai import OpenAI

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

A2_PARTS = [
    "Teil 1 – Fragen zu Schlüsselwörtern",
    "Teil 2 – Bildbeschreibung & Diskussion",
    "Teil 3 – Gemeinsam planen"
]
A2_TOPICS = {
    A2_PARTS[0]: ["Wohnort", "Tagesablauf"],
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

def get_ai_system_prompt(mode, level, teil, topic, custom_intro_done):
    return f"You are Herr Felix. Mode: {mode}, Level: {level}, Part: {teil}, Topic: {topic}"

def get_recent_message_history(messages, N=6):
    return messages[-N:] if len(messages) > N else messages

def chat_with_openai(system_prompt, message_history, api_key="sk-..."):
    # Placeholder for OpenAI call. Uncomment and use your OpenAI key:
    # client = OpenAI(api_key=api_key)
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

def step_1_login():
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️", key="stage1_next"):
        st.session_state["student_code"] = code.strip().lower()
        st.session_state["step"] = 2
        st.experimental_rerun()
        return

def step_2_welcome():
    st.success("Welcome to Falowen!")
    if st.button("Next ➡️", key="stage2_next"):
        st.session_state["step"] = 3
        st.experimental_rerun()
        return

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
        st.experimental_rerun()
        return

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
        mode = st.session_state.get("selected_mode", "")
        level = st.session_state.get("selected_exam_level") or st.session_state.get("custom_chat_level")
        teil = st.session_state.get("selected_teil")
        topic = st.session_state.get("initial_prompt", "")
        custom_intro_done = st.session_state.get("custom_topic_intro_done", False)
        system_prompt = get_ai_system_prompt(mode, level, teil, topic, custom_intro_done)
        message_history = get_recent_message_history(st.session_state["messages"], N=6)
        ai_reply = chat_with_openai(system_prompt, message_history)  # Add api_key as needed
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
        st.experimental_rerun()
        return
    if st.button("Summary / Restart"):
        st.session_state["step"] = 6
        st.experimental_rerun()
        return

def step_6_summary():
    st.success("Session complete! 🎉")
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
