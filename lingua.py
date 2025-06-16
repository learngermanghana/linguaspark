import streamlit as st
import pandas as pd
import random
from datetime import date
import os
import time

# ------------------- Branding -------------------
st.markdown("""
<div style='display:flex;align-items:center;gap:18px;margin-bottom:22px;'>
    <img src='https://cdn-icons-png.flaticon.com/512/6815/6815043.png' width='54' style='border-radius:50%;border:2.5px solid #51a8d2;box-shadow:0 2px 8px #cbe7fb;'/>
    <div>
        <span style='font-size:2.1rem;font-weight:bold;color:#17617a;letter-spacing:2px;'>Falowen</span><br>
        <span style='font-size:1.08rem;color:#268049;'>Your personal German speaking coach (Herr Felix)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------- App Data -------------------
CODES_FILE = "student_codes.csv"
TEACHER_PASSWORD = "Felix029"
DAILY_LIMIT = 25
MAX_TURNS = 10

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

# ------------------- Session State Init -------------------
def init_session():
    defaults = {
        "step": 1, "student_code": "", "messages": [],
        "turn_count": 0, "selected_mode": None, "selected_exam_level": None,
        "selected_teil": None, "initial_prompt": None,
        "teacher_authenticated": False, "daily_usage": {},
        "presentation_mode": False, "presentation_topic": None, "custom_chat_level": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_session()

# ------------------- Teacher Admin Sidebar -------------------
with st.sidebar.expander("👩‍🏫 Teacher Area (Login/Settings)", expanded=False):
    if not st.session_state["teacher_authenticated"]:
        pwd = st.text_input("Teacher Login (for admin only)", type="password")
        if st.button("Login (Teacher)"):
            if pwd == TEACHER_PASSWORD:
                st.session_state["teacher_authenticated"] = True
                st.success("Access granted!")
            elif pwd:
                st.error("Incorrect password. Please try again.")
    else:
        st.header("👩‍🏫 Teacher Dashboard")
        df_codes = pd.read_csv(CODES_FILE) if os.path.exists(CODES_FILE) else pd.DataFrame(columns=["code"])
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

# ------------------- Utility Functions -------------------
def show_formatted_ai_reply(ai_reply):
    # Split sections for: answer, correction, grammar tip, next question
    lines = [l.strip() for l in ai_reply.split('\n') if l.strip()]
    main, correction, grammatik, followup = '', '', '', ''
    curr_section = 'main'
    for line in lines:
        header = line.lower()
        if header.startswith('correction:'):
            curr_section = 'correction'
            line = line.split(':',1)[-1].strip()
            correction += (line + ' ') if line else ''
            continue
        elif header.startswith('grammar tip:') or header.startswith('grammatik-tipp:'):
            curr_section = 'grammatik'
            line = line.split(':',1)[-1].strip()
            grammatik += (line + ' ') if line else ''
            continue
        elif header.startswith('next question:') or header.startswith('folgefrage'):
            curr_section = 'followup'
            line = line.split(':',1)[-1].strip()
            followup += (line + ' ') if line else ''
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

def get_ai_system_prompt(topic, mode, level, teil):
    return (
        f"You are Herr Felix, a Goethe examiner. "
        f"Topic: {topic} "
        "1. Answer in simple German.\n"
        "2. If student makes a mistake, give Correction: ...\n"
        "3. Give Grammar Tip: ...\n"
        "4. Next question: ...\n"
        "Use these sections exactly!"
    )

def chat_with_openai(system_prompt, message_history):
    # Replace with real OpenAI API in prod
    return (
        "Guten Morgen! Ich stehe jeden Tag um 7 Uhr auf. Dann frühstücke ich.\n"
        "Correction: Ich stehe jeden Tag um 7 Uhr **auf** (verb at the end).\n"
        "Grammar Tip: In separable verbs, the prefix goes to the end.\n"
        "Next question: Was machst du nach dem Frühstück?"
    )

# ------------------- Step Functions -------------------
def step_1_login():
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️"):
        code_clean = code.strip().lower()
        df_codes = pd.read_csv(CODES_FILE) if os.path.exists(CODES_FILE) else pd.DataFrame(columns=["code"])
        if code_clean in df_codes["code"].dropna().tolist():
            st.session_state["student_code"] = code_clean
            st.session_state["step"] = 2
        else:
            st.error("This code is not recognized. Please check with your tutor.")

def step_2_welcome():
    st.success("Welcome to Falowen!")
    if st.button("Next ➡️"):
        st.session_state["step"] = 3

def step_3_mode():
    mode = st.radio(
        "Choose your practice mode:",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)", "Präsentation (B1/A2)"],
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode
    if st.button("Next ➡️"):
        if mode == "Präsentation (B1/A2)":
            st.session_state["presentation_mode"] = True
            st.session_state["step"] = 7
        else:
            st.session_state["presentation_mode"] = False
            st.session_state["step"] = 4 if mode == "Geführte Prüfungssimulation (Exam Mode)" else 5

def step_4_exam_part():
    st.markdown("### 📝 Prüfungsteil wählen / Choose exam part")
    exam_level = st.radio("Exam Level:", ["A2", "B1"], key="exam_level_select")
    st.session_state["selected_exam_level"] = exam_level
    part_options = A2_PARTS if exam_level == "A2" else B1_PARTS
    topics_dict = A2_TOPICS if exam_level == "A2" else B1_TOPICS
    teil = st.selectbox("Part to practice:", part_options)
    st.session_state["selected_teil"] = teil
    current_topics = topics_dict[teil]
    selected_topic = st.selectbox("Choose a topic:", current_topics)
    if st.button("Start Chat ➡️"):
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
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(msg["content"])
    user_input = st.chat_input("💬 Type your answer here...")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("assistant", avatar="🧑‍🏫"):
            st.markdown("<span style='color:#2277bb;font-style:italic'>Herr Felix is typing ...</span>", unsafe_allow_html=True)
        time.sleep(1.3)
        prompt = get_ai_system_prompt(
            st.session_state["initial_prompt"],
            st.session_state["selected_mode"],
            st.session_state.get("selected_exam_level", "A2"),
            st.session_state.get("selected_teil", "Teil 1")
        )
        ai_reply = chat_with_openai(prompt, st.session_state["messages"][-5:])
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
        st.experimental_rerun()
    if st.button("Summary / Restart"):
        st.session_state["step"] = 6

def step_7_presentation():
    st.header("🎤 Präsentation Practice")
    topic = st.text_input("Enter your Präsentation topic:", value=st.session_state["presentation_topic"] or "")
    if topic:
        st.session_state["presentation_topic"] = topic
        if not st.session_state["messages"]:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"Bitte beginne deine Präsentation zum Thema **{topic}**."
            })
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                show_formatted_ai_reply(msg["content"])
        else:
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(msg["content"])
    user_input = st.chat_input("Type your next part of the presentation...")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("assistant", avatar="🧑‍🏫"):
            st.markdown("<span style='color:#2277bb;font-style:italic'>Herr Felix is typing ...</span>", unsafe_allow_html=True)
        time.sleep(1.3)
        prompt = get_ai_system_prompt(
            st.session_state["presentation_topic"], "Präsentation", "B1", "Präsentation"
        )
        ai_reply = chat_with_openai(prompt, st.session_state["messages"][-5:])
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
        st.experimental_rerun()
    if st.button("Summary / Restart", key="pres_sum_restart"):
        st.session_state["step"] = 6
        st.session_state["presentation_topic"] = None
        st.session_state["messages"] = []

def step_6_summary():
    st.success("Session complete! 🎉")
    if st.button("Restart"):
        st.session_state["step"] = 1
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["custom_chat_level"] = None
        st.session_state["presentation_topic"] = None

# ------------------- Dispatcher -------------------
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
elif step == 7:
    step_7_presentation()
