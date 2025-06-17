import streamlit as st
from openai import OpenAI
import tempfile
import random
import pandas as pd
import os
from datetime import date
import time
import re

# --- Helper ---
def _trim_history(history, max_chars=12000):
    """Return the most recent messages that fit within max_chars."""
    total = 0
    trimmed = []
    for msg in reversed(history):
        content = msg.get("content", "")
        msg_len = len(content)
        if total + msg_len > max_chars:
            break
        trimmed.append(msg)
        total += msg_len
    return list(reversed(trimmed))

# --- CONFIG ---
st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---- HEADER ----
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

# --- CONSTANTS ---
CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
MAX_TURNS = 10
TEACHER_PASSWORD = "Felix029"

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
ALL_KEYWORDS = set([
    "Freizeit", "Familie", "Essen", "Reisen", "Hobbys", "Sport",
    "Wochenende", "Arbeit", "Haustiere", "Sprachen", "Schule"
])

# --- TEACHER AREA ---
def load_codes():
    if os.path.exists(CODES_FILE):
        df = pd.read_csv(CODES_FILE)
        if "code" not in df.columns:
            df = pd.DataFrame(columns=["code"])
        df["code"] = df["code"].astype(str).str.strip().str.lower()
    else:
        df = pd.DataFrame(columns=["code"])
    return df

with st.sidebar.expander("👩‍🏫 Teacher Area (Login/Settings)", expanded=False):
    if "teacher_authenticated" not in st.session_state:
        st.session_state["teacher_authenticated"] = False
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
        df_codes = load_codes()
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

# --- SESSION STATE DEFAULTS ---
if "step" not in st.session_state: st.session_state["step"] = 1
if "student_code" not in st.session_state: st.session_state["student_code"] = ""
if "daily_usage" not in st.session_state: st.session_state["daily_usage"] = {}
if "messages" not in st.session_state: st.session_state["messages"] = []
if "turn_count" not in st.session_state: st.session_state["turn_count"] = 0
if "used_keywords" not in st.session_state: st.session_state["used_keywords"] = set()
if "used_topics" not in st.session_state: st.session_state["used_topics"] = set()
if "current_topic" not in st.session_state: st.session_state["current_topic"] = None
if "intro_key" not in st.session_state: st.session_state["intro_key"] = ""

# --- MAIN FLOW ---
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

elif st.session_state["step"] == 2:
    st.success(f"**Did you know?** Every session is exam-like and personalized by Herr Felix! 🚀")
    st.markdown("<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor, Herr Felix!</h2>", unsafe_allow_html=True)
    st.info("""
        🎤 This is not just chat—it's your personal exam preparation bootcamp!  
        Practice A2 and B1 speaking, presentations, and custom topics.  
        Get feedback, corrections, grammar tips, and exam-style questions.
        """)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage2_back"):
            st.session_state["step"] = 1
    with col2:
        if st.button("Next ➡️", key="stage2_next"):
            st.session_state["step"] = 3

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
    with col2:
        if st.button("Next ➡️", key="stage3_next"):
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["used_keywords"] = set()
            st.session_state["used_topics"] = set()
            st.session_state["current_topic"] = None
            if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                st.session_state["step"] = 5
            else:
                st.session_state["step"] = 4

elif st.session_state["step"] == 4:
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
            # Pick first topic for Teil 2 (random from A2/B1 list, not yet used)
            if exam_level == "A2" and teil.startswith("Teil 2"):
                remaining = list(set(A2_TEIL2) - st.session_state["used_topics"])
                topic = random.choice(remaining)
                st.session_state["current_topic"] = topic
                prompt = f"**A2 Teil 2:** Erzähle über das Thema: **{topic}**."
            elif exam_level == "B1" and teil.startswith("Teil 2"):
                remaining = list(set(B1_TEIL2) - st.session_state["used_topics"])
                topic = random.choice(remaining)
                st.session_state["current_topic"] = topic
                prompt = f"**B1 Teil 2:** Halte eine Präsentation über das Thema: **{topic}**."
            else:
                prompt = "Starte das Gespräch."
            st.session_state["initial_prompt"] = prompt
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["step"] = 5

# --------------- FEEDBACK CARD FUNCTION ------------------
def show_feedback_card(ai_reply):
    """
    Expects ai_reply as a multi-line string with keys: 'Answer:', 'Correction:', 'Grammar Tip:', 'Next question:'
    """
    def extract(section, text):
        pattern = rf"{section}:(.*?)(?:\n[A-Z][^:]*:|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""
    answer      = extract("Answer", ai_reply)      or "–"
    correction  = extract("Correction", ai_reply)  or "No correction needed!"
    grammar_tip = extract("Grammar Tip", ai_reply) or "No grammar tip needed!"
    next_q      = extract("Next question", ai_reply) or "–"
    st.markdown(f"""
    <div style='background:#f6f6fa; border-radius:16px; padding:18px 22px; margin:12px 0; box-shadow:0 2px 8px #dde0f3;'>
        <div style='font-size:1.13rem;'><span style="font-size:1.22rem;">🟩</span> <b>Your answer:</b> {answer}</div>
        <div style='color:#d84315;font-size:1.06rem;margin-top:4px;'><span style="font-size:1.12rem;">✏️</span> <b>Correction:</b> {correction}</div>
        <div style='color:#1976d2;font-size:1.06rem;margin-top:4px;'><span style="font-size:1.12rem;">📚</span> <b>Tip:</b> {grammar_tip}</div>
        <div style='color:#388e3c;font-size:1.11rem;margin-top:7px;'><span style="font-size:1.15rem;">❓</span> <b>Next task:</b> {next_q}</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- STEP 5: MAIN CHAT LOGIC + INTRO SCREENS ------------------------
if st.session_state["step"] == 5:
    def get_intro_text(mode, level):
        if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
            if level == "A2":
                return """
                <h3>🗨️ A2 Custom Chat</h3>
                <ul>
                  <li>Du kannst über <b>jedes Thema</b> schreiben (z.B. "Wochenende", "Familie").</li>
                  <li>Herr Felix hilft dir, gibt Feedback und stellt passende Fragen.</li>
                  <li>Nutze einfache Sätze und habe Spaß!</li>
                </ul>
                """
            else:
                return """
                <h3>🗨️ B1 Custom Chat</h3>
                <ul>
                  <li>Trainiere deine <b>B1 Präsentation</b> und Meinungsäußerung.</li>
                  <li>Wähle ein Thema (z.B. "Umwelt", "Technologie") und antworte Schritt für Schritt.</li>
                  <li>Herr Felix fragt nach Meinung, Vorteil/Nachteil, Situation im Heimatland usw.</li>
                </ul>
                """
        else:
            if level == "A2":
                return """
                <h3>📝 A2 Prüfungssimulation</h3>
                <ul>
                  <li>Übe wie in der echten A2-Prüfung: kurze Antworten, Alltagsthemen.</li>
                  <li>Folge genau den Anweisungen und Tipps.</li>
                </ul>
                """
            else:
                return """
                <h3>📝 B1 Prüfungssimulation</h3>
                <ul>
                  <li>Simuliere Präsentation, Meinung und Diskussion wie in der B1-Prüfung.</li>
                  <li>Du bekommst gezielte Aufgaben, Feedback und Korrekturen.</li>
                </ul>
                """
    # --- Custom Chat: Ask for level if not chosen yet
    mode = st.session_state.get("selected_mode", "Eigenes Thema/Frage (Custom Topic Chat)")
    if mode == "Eigenes Thema/Frage (Custom Topic Chat)" and not st.session_state.get("custom_chat_level"):
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
                "content": "Hallo! 👋 What would you like to talk about? Give me details of what you want so I can understand."
            }]
        st.stop()
    # --- Custom Intro per mode/level (shows once)
    level = (
        st.session_state.get("custom_chat_level", "A2")
        if mode.startswith("Eigenes")
        else st.session_state.get("selected_exam_level", "A2")
    )
    intro_key = f"{mode}-{level}"
    if st.session_state["intro_key"] != intro_key:
        st.markdown(get_intro_text(mode, level), unsafe_allow_html=True)
        if st.button("Los geht's!"):
            st.session_state["intro_key"] = intro_key
            st.rerun()
        st.stop()

    # ========== MAIN CHAT LOGIC ==========
    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    st.session_state["daily_usage"].setdefault(usage_key, 0)
    session_ended = st.session_state["turn_count"] >= MAX_TURNS
    used_today = st.session_state["daily_usage"][usage_key]
    # Initial AI prompt for exam or custom chat (if needed)
    if not st.session_state["messages"]:
        first_prompt = st.session_state.get("initial_prompt") or "Worüber möchtest du sprechen?"
        st.session_state["messages"].append({"role": "assistant", "content": first_prompt})

    # -- User input (audio/text)
    typed = st.chat_input("💬 Oder tippe deine Antwort hier...", key="stage5_typed_input")
    user_input = typed
    if user_input and not session_ended:
        if used_today >= DAILY_LIMIT:
            st.warning(
                "You’ve reached today’s free practice limit. "
                "Please come back tomorrow or contact your tutor!"
            )
        else:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown("<i>Herr Felix is typing ...</i>", unsafe_allow_html=True)
            time.sleep(1.2)

            # --- CONTEXTUAL MEMORY ---
            last_user = user_input
            for word in ALL_KEYWORDS:
                if word.lower() in last_user.lower():
                    st.session_state["used_keywords"].add(word)

            # --- For Exam Mode: Random next topic after a certain # of turns or "next" detected ---
            next_topic = None
            exam_mode = mode.startswith("Geführte") and level in ["A2", "B1"]
            if exam_mode and st.session_state["current_topic"]:
                # After 3 turns or if student writes "fertig" or "next", switch topic
                if (st.session_state["turn_count"] % 3 == 0) or any(
                    trigger in last_user.lower() for trigger in ["fertig", "next", "weiter"]
                ):
                    # Add current to used, choose new
                    st.session_state["used_topics"].add(st.session_state["current_topic"])
                    topic_list = A2_TEIL2 if level == "A2" else B1_TEIL2
                    remaining = list(set(topic_list) - st.session_state["used_topics"])
                    if remaining:
                        next_topic = random.choice(remaining)
                        st.session_state["current_topic"] = next_topic
                    else:
                        next_topic = None
                        st.session_state["current_topic"] = None

            # --- REAL-LIFE MINI-CHALLENGE every 4th turn
            mini_challenges = [
                "Mini Challenge: Stell dir vor, du bist im Supermarkt und findest die Milch nicht. Was sagst du, um Hilfe zu bekommen?",
                "Mini Challenge: Dein Freund ruft dich an und fragt, was du am Wochenende machst. Was antwortest du?",
                "Mini Challenge: Du bist im Restaurant und das Essen schmeckt dir nicht. Was würdest du dem Kellner sagen?",
                "Mini Challenge: Stell dir vor, du hast deinen Schlüssel verloren. Wen rufst du an und was sagst du?",
                "Mini Challenge: Du willst eine Fahrkarte kaufen. Was sagst du am Schalter?",
            ]
            scenario = ""
            if st.session_state["turn_count"] % 4 == 0 and st.session_state["turn_count"] > 0:
                scenario = random.choice(mini_challenges)

            # --- System Prompt (enforces answer structure) ---
            ai_system_prompt = (
                "You are Herr Felix, a strict but friendly German teacher/examiner."
                " ALWAYS reply in this structure:"
                "\nAnswer: (A short positive statement about the student's last answer. No questions here.)"
                "\nCorrection: (Show a corrected version of the student's answer, or say 'No correction needed!')"
                "\nGrammar Tip: (A short, relevant grammar tip, or 'No grammar tip needed!')"
                "\nNext question: (ONE new question or mini-challenge, in German, about the same or next topic. No more than one question per reply.)"
            )
            # Add context and challenges
            already = ", ".join(sorted(st.session_state["used_keywords"])) or "nothing yet"
            not_yet = ", ".join(sorted(ALL_KEYWORDS - st.session_state["used_keywords"])) or "all main topics done"
            ai_system_prompt += (
                f"\nWe already talked about: {already}. "
                f"Do NOT repeat those topics unless referencing the student's previous answers. "
                f"Ask a question about a topic not yet discussed: {not_yet}. "
            )
            if scenario:
                ai_system_prompt += f"\n{scenario}"
            if next_topic:
                ai_system_prompt += f"\nNext topic: {next_topic}"

            # --- OpenAI Chat Completion ---
            trimmed = _trim_history(st.session_state["messages"])
            conversation = [{"role": "system", "content": ai_system_prompt}] + trimmed
            with st.spinner("🧑‍🏫 Herr Felix is typing..."):
                try:
                    client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                    resp = client.chat.completions.create(
                        model="gpt-4o", messages=conversation
                    )
                    ai_reply = resp.choices[0].message.content
                except Exception as e:
                    ai_reply = "Sorry, there was a problem generating a response."
                    st.error(str(e))
            st.session_state["messages"].append(
                {"role": "assistant", "content": ai_reply}
            )

    # --- Display Chat with Feedback Cards ---
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(
                    "<span style='color:#33691e;font-weight:bold'>🧑‍🏫 Herr Felix:</span>",
                    unsafe_allow_html=True
                )
                show_feedback_card(msg["content"])
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- Navigation buttons ---
    def reset_to_prev():
        prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
        st.session_state.update({
            "step": prev,
            "messages": [],
            "turn_count": 0,
            "used_keywords": set(),
            "used_topics": set(),
            "custom_chat_level": None,
            "intro_key": "",
            "current_topic": None,
        })
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            reset_to_prev()
    with col2:
        if session_ended and st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6

elif st.session_state["step"] == 6:
    st.header("Session Summary")
    st.markdown(
        "Vielen Dank fürs Üben mit **Herrn Felix**! Hier ist eine kurze Übersicht Ihrer Session:")

    keywords = ", ".join(sorted(st.session_state.get("used_keywords", []))) or "–"
    topics = ", ".join(sorted(st.session_state.get("used_topics", []))) or "–"
    turns = st.session_state.get("turn_count", 0)

    st.write(f"**Gesprochene Runden:** {turns}")
    st.write(f"**Benutzte Schlüsselwörter:** {keywords}")
    st.write(f"**Bearbeitete Themen:** {topics}")

    st.success("Bis zum nächsten Mal und viel Erfolg beim Lernen!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Back to Start", key="stage6_restart"):
            st.session_state.update({
                "step": 1,
                "messages": [],
                "turn_count": 0,
                "used_keywords": set(),
                "used_topics": set(),
                "custom_chat_level": None,
                "intro_key": "",
                "current_topic": None,
            })
    with col2:
        if st.button("Exit", key="stage6_exit"):
            st.write("👋 Bis bald! Du kannst das Fenster nun schließen.")
            st.stop()

# --- END ---
