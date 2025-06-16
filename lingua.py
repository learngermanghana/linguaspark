import streamlit as st
import random
from datetime import date
import pandas as pd
import os
import time
import tempfile

# --- Falowen Branding ---
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

# --- Exam Data ---
A2_PARTS = ["Teil 1 – Fragen zu Schlüsselwörtern", "Teil 2 – Bildbeschreibung & Diskussion", "Teil 3 – Gemeinsam planen"]
A2_TOPICS = {
    A2_PARTS[0]: ["Wohnort", "Tagesablauf", "Freizeit"],
    A2_PARTS[1]: ["Was machen Sie am Wochenende?"],
    A2_PARTS[2]: ["Zusammen ins Kino gehen"]
}
B1_PARTS = ["Teil 1 – Gemeinsam planen (Dialogue)", "Teil 2 – Präsentation (Monologue)", "Teil 3 – Feedback & Fragen stellen"]
B1_TOPICS = {
    B1_PARTS[0]: ["Mithilfe beim Sommerfest"],
    B1_PARTS[1]: ["Ausbildung"],
    B1_PARTS[2]: ["Fragen stellen zu einer Präsentation"]
}
CODES_FILE = "student_codes.csv"
TEACHER_PASSWORD = "Felix029"
DAILY_LIMIT = 25
MAX_TURNS = 10

def init_session():
    defaults = {
        "step": 1, "student_code": "", "messages": [],
        "turn_count": 0, "selected_mode": None, "selected_exam_level": None,
        "selected_teil": None, "initial_prompt": None,
        "custom_chat_level": None, "custom_topic_intro_done": False,
        "teacher_authenticated": False, "daily_usage": {},
        "herr_felix_typing": False, "presentation_mode": False,
        "presentation_topic": None, "presentation_progress": 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_session()

# --- Teacher Admin Sidebar ---
with st.sidebar.expander("👩‍🏫 Teacher Area (Login/Settings)", expanded=False):
    if not st.session_state["teacher_authenticated"]:
        pwd = st.text_input("Teacher Login (for admin only)", type="password")
        login_btn = st.button("Login (Teacher)")
        if login_btn:
            if pwd == TEACHER_PASSWORD:
                st.session_state["teacher_authenticated"] = True
                st.success("Access granted!")
            elif pwd != "":
                st.error("Incorrect password. Please try again.")
    else:
        st.header("👩‍🏫 Teacher Dashboard")
        df_codes = pd.read_csv(CODES_FILE) if os.path.exists(CODES_FILE) else pd.DataFrame(columns=["code"])
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

def get_ai_system_prompt(mode, level, teil, topic, custom_intro_done, presentation_mode):
    if presentation_mode:
        # You can make this even smarter: rotate opinion, vorteil, nachteil, Heimatland, summary, etc.
        return (
            f"You are Herr Felix, a German B1 examiner. "
            f"The student is giving a presentation on: {topic}. "
            "Let them speak, give gentle tips and ask only ONE follow-up at a time. "
            "Format: Answer, Correction (if any), Grammar Tip (EN), Next question."
        )
    # ... (keep the rest as in previous examples, for brevity)

    return "You are Herr Felix. Answer in German."

def chat_with_openai(system_prompt, message_history):
    # FAKE "real" AI: Use OpenAI here in production
    # import openai; client = openai.OpenAI(api_key=...)
    # ...see above for real call...
    if "presentation" in system_prompt.lower():
        return (
            "Danke für Ihre Präsentation über Ausbildung!\n"
            "Correction: Keine Fehler.\n"
            "Grammar Tip: Achten Sie auf den Gebrauch von Artikeln.\n"
            "Next question: Was war der größte Vorteil für Sie?"
        )
    # fallback generic
    return (
        "Guten Morgen! Ich stehe jeden Tag um 7 Uhr auf. Dann frühstücke ich.\n"
        "Correction: Ich stehe jeden Tag um 7 Uhr **auf** (verb at the end).\n"
        "Grammar Tip: In separable verbs, the prefix goes to the end.\n"
        "Next question: Was machst du nach dem Frühstück?"
    )

def show_formatted_ai_reply(ai_reply):
    lines = [l.strip() for l in ai_reply.split('\n') if l.strip()]
    main, correction, grammatik, followup = '', '', '', ''
    curr_section = 'main'
    for line in lines:
        header = line.lower()
        if header.startswith('correction:') or header.startswith('- correction:'):
            curr_section = 'correction'; line = line.split(':',1)[-1].strip()
            if line: correction += line + ' '; continue
        elif header.startswith('grammar tip:') or header.startswith('- grammar tip:') or header.startswith('grammatik-tipp:') or header.startswith('- grammatik-tipp:'):
            curr_section = 'grammatik'; line = line.split(':',1)[-1].strip()
            if line: grammatik += line + ' '; continue
        elif header.startswith('next question:') or header.startswith('- next question:') or header.startswith('follow-up question') or header.startswith('folgefrage'):
            curr_section = 'followup'; line = line.split(':',1)[-1].strip()
            if line: followup += line + ' '; continue
        if curr_section == 'main': main += line + ' '
        elif curr_section == 'correction': correction += line + ' '
        elif curr_section == 'grammatik': grammatik += line + ' '
        elif curr_section == 'followup': followup += line + ' '

    st.markdown(f"<div style='background:#eafbf7;border-radius:1.5em;padding:1em 1.4em;margin-bottom:0.6em'><b>🧑‍🏫 Herr Felix:</b><br>{main.strip()}</div>", unsafe_allow_html=True)
    if correction.strip():
        st.markdown(f"<div style='color:#c62828'><b>✏️ Correction:</b> {correction.strip()}</div>", unsafe_allow_html=True)
    if grammatik.strip():
        st.markdown(f"<div style='color:#1565c0'><b>📚 Grammar Tip:</b> {grammatik.strip()}</div>", unsafe_allow_html=True)
    if followup.strip():
        st.markdown(f"<div style='color:#388e3c'><b>➡️ Next question:</b> {followup.strip()}</div>", unsafe_allow_html=True)

def show_user_bubble(content):
    st.markdown(f"<div style='background:#f2f7fa;border-radius:1.3em;padding:1em 1.4em;margin-bottom:0.7em;text-align:right'><b>🧑‍🎓 You:</b><br>{content}</div>", unsafe_allow_html=True)

def step_1_login():
    st.title("Student Login")
    code = st.text_input("🔑 Enter your student code to begin:")
    if st.button("Next ➡️", key="stage1_next"):
        code_clean = code.strip().lower()
        df_codes = pd.read_csv(CODES_FILE) if os.path.exists(CODES_FILE) else pd.DataFrame(columns=["code"])
        if code_clean in df_codes["code"].dropna().tolist():
            st.session_state["student_code"] = code_clean
            st.session_state["step"] = 2
        else:
            st.error("This code is not recognized. Please check with your tutor.")

def step_2_welcome():
    st.success("Welcome to Falowen!")
    if st.button("Next ➡️", key="stage2_next"):
        st.session_state["step"] = 3

def step_3_mode():
    mode = st.radio(
        "Choose your practice mode:",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)", "Präsentation (B1/A2)"],
        key="mode_selector"
    )
    st.session_state["selected_mode"] = mode
    if st.button("Next ➡️", key="stage3_next"):
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
    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(usage_key, 0)
    used_today = st.session_state["daily_usage"][usage_key]
    st.info(
        f"Student code: `{student_code}` | "
        f"Today's practice: {used_today}/{DAILY_LIMIT}"
    )
    # Chat history as bubbles
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            show_formatted_ai_reply(msg["content"])
        else:
            show_user_bubble(msg["content"])
    # Typing indicator
    if st.session_state.get("herr_felix_typing"):
        st.markdown("<span style='color:#2277bb;font-style:italic'>🧑‍🏫 Herr Felix is typing ...</span>", unsafe_allow_html=True)
    # Input UI
    typed = st.chat_input("💬 Type your answer here...", key="stage5_typed_input")
    if typed:
        st.session_state["messages"].append({"role": "user", "content": typed})
        st.session_state["herr_felix_typing"] = True
        st.experimental_rerun()  # will trigger the typing indicator on reload
    if st.session_state.get("herr_felix_typing") and len(st.session_state["messages"]) > 0 and st.session_state["messages"][-1]["role"] == "user":
        # Simulate typing delay
        time.sleep(1.2)
        mode = st.session_state.get("selected_mode", "")
        level = st.session_state.get("selected_exam_level") or st.session_state.get("custom_chat_level")
        teil = st.session_state.get("selected_teil")
        topic = st.session_state.get("initial_prompt", "")
        custom_intro_done = st.session_state.get("custom_topic_intro_done", False)
        presentation_mode = st.session_state.get("presentation_mode", False)
        system_prompt = get_ai_system_prompt(mode, level, teil, topic, custom_intro_done, presentation_mode)
        message_history = st.session_state["messages"][-6:]
        ai_reply = chat_with_openai(system_prompt, message_history)
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
        st.session_state["herr_felix_typing"] = False
        st.experimental_rerun()
    if st.button("Summary / Restart"):
        st.session_state["step"] = 6

def step_7_presentation():
    st.header("🎤 Präsentation Practice")
    st.info("You are in presentation mode. Type your B1/A2 Präsentation on your chosen topic, and Herr Felix will interact as the examiner with detailed feedback, questions, and tips.")
    if not st.session_state["presentation_topic"]:
        st.session_state["presentation_topic"] = st.text_input("Enter your topic:")
        if st.session_state["presentation_topic"]:
            st.session_state["messages"] = []
            st.session_state["presentation_progress"] = 0
    else:
        st.write(f"**Your topic:** {st.session_state['presentation_topic']}")
        # Display history
        for msg in st.session_state["messages"]:
            if msg["role"] == "assistant":
                show_formatted_ai_reply(msg["content"])
            else:
                show_user_bubble(msg["content"])
        # Typing indicator
        if st.session_state.get("herr_felix_typing"):
            st.markdown("<span style='color:#2277bb;font-style:italic'>🧑‍🏫 Herr Felix is typing ...</span>", unsafe_allow_html=True)
        typed = st.chat_input("Type your next part of the presentation or answer Herr Felix's question...", key="presentation_input")
        if typed:
            st.session_state["messages"].append({"role": "user", "content": typed})
            st.session_state["herr_felix_typing"] = True
            st.experimental_rerun()
        if st.session_state.get("herr_felix_typing") and len(st.session_state["messages"]) > 0 and st.session_state["messages"][-1]["role"] == "user":
            time.sleep(1.1)
            # Presentation prompt logic
            mode = st.session_state.get("selected_mode", "")
            level = st.session_state.get("selected_exam_level") or "B1"
            teil = None
            topic = st.session_state["presentation_topic"]
            custom_intro_done = False
            presentation_mode = True
            system_prompt = get_ai_system_prompt(mode, level, teil, topic, custom_intro_done, presentation_mode)
            message_history = st.session_state["messages"][-6:]
            ai_reply = chat_with_openai(system_prompt, message_history)
            st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
            st.session_state["herr_felix_typing"] = False
            st.experimental_rerun()
        if st.button("Summary / Restart", key="pres_sum_restart"):
            st.session_state["step"] = 6
            st.session_state["presentation_topic"] = None

def step_6_summary():
    st.success("Session complete! 🎉")
    if st.button("Restart", key="summary_restart"):
        st.session_state["step"] = 1
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["custom_chat_level"] = None
        st.session_state["custom_topic_intro_done"] = False
        st.session_state["presentation_topic"] = None

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
elif step == 7:
    step_7_presentation()
