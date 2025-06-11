import streamlit as st
from openai import OpenAI
import tempfile
import io
from gtts import gTTS
import random
import pandas as pd
import os
from datetime import date
import re

# Streamlit page config
st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="expanded"
)

# File/database constants
CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
max_turns = 6
TEACHER_PASSWORD = "Felix029"

# Exam topic lists
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
# STAGE 2: Teacher Area Sidebar & Session State Setup

# ---- Teacher Dashboard (Sidebar) ----
with st.sidebar.expander("👩‍🏫 Teacher Area (Login/Settings)", expanded=False):
    if "teacher_authenticated" not in st.session_state:
        st.session_state["teacher_authenticated"] = False

    # Teacher login prompt
    if not st.session_state["teacher_authenticated"]:
        st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
        pwd = st.text_input("Teacher Login (for admin only)", type="password")
        login_btn = st.button("Login (Teacher)")
        if login_btn:
            if pwd == TEACHER_PASSWORD:
                st.session_state["teacher_authenticated"] = True
                st.success("Access granted!")
            elif pwd != "":
                st.error("Incorrect password. Please try again.")

    # Teacher dashboard/settings
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

# ---- Global session state for app navigation ----
if "step" not in st.session_state:
    st.session_state["step"] = 1
if "student_code" not in st.session_state:
    st.session_state["student_code"] = ""
if "daily_usage" not in st.session_state:
    st.session_state["daily_usage"] = {}
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "corrections" not in st.session_state:
    st.session_state["corrections"] = []
if "turn_count" not in st.session_state:
    st.session_state["turn_count"] = 0
# STAGE 3: Student Login, Welcome, and Mode Selection

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
        "🇬🇭 Herr Felix was born in Ghana and mastered German up to C1 level!",
        "🎓 Herr Felix studied International Management at IU International University in Germany.",
        "🏫 He founded Learn Language Education Academy to help students pass Goethe exams.",
        "💡 Herr Felix used to run a record label and produce music before becoming a language coach!",
        "🥇 He loves making language learning fun, personal, and exam-focused.",
        "📚 Herr Felix speaks English, German, and loves teaching in both.",
        "🚀 Sometimes Herr Felix will throw in a real Goethe exam question—are you ready?",
        "🤖 Herr Felix built this app himself—so every session is personalized!"
    ]
    st.success(f"**Did you know?** {random.choice(fun_facts)}")
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

# ------ Stage 3: Mode Selection ------
elif st.session_state["step"] == 3:
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
        custom_topic = st.text_input("Type your own topic or question here...", value=st.session_state.get("custom_topic", ""), key="custom_topic_input")
        st.session_state["custom_topic"] = custom_topic
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage3_back"):
            st.session_state["step"] = 2
    with col2:
        if st.button("Next ➡️", key="stage3_next"):
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                st.session_state["step"] = 5
            else:
                st.session_state["step"] = 4
# STAGE 4: Exam Part Selection

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
            st.session_state["initial_prompt"] = prompt
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["step"] = 5
            
import re

def show_formatted_ai_reply(ai_reply):
    # Split into sections by your AI format
    correction = ""
    grammatik = ""
    followup = ""
    main_reply = ai_reply

    # Try to extract by label (for your format)
    correction_match = re.search(r'Correction:\s*(.*?)\n- Grammatik-Tipp:', ai_reply, re.DOTALL)
    grammatik_match = re.search(r'- Grammatik-Tipp:\s*(.*?)\n- Follow-up question', ai_reply, re.DOTALL)
    followup_match = re.search(r'- Follow-up question\s*(.*)', ai_reply, re.DOTALL)
    
    if correction_match:
        correction = correction_match.group(1).strip()
    if grammatik_match:
        grammatik = grammatik_match.group(1).strip()
    if followup_match:
        followup = followup_match.group(1).strip()
    
    # The main reply is before "Correction:" if it exists
    if "Correction:" in ai_reply:
        main_reply = ai_reply.split("Correction:")[0].strip()

    # Display each section with color and headings
    st.markdown(f"**📝 Antwort:**<br>{main_reply}", unsafe_allow_html=True)
    if correction:
        st.markdown(f"<div style='color:#c62828'><b>✏️ Korrektur:</b><br>{correction}</div>", unsafe_allow_html=True)
    if grammatik:
        st.markdown(f"<div style='color:#1565c0'><b>📚 Grammatik-Tipp:</b><br>{grammatik}</div>", unsafe_allow_html=True)
    if followup:
        st.markdown(f"<div style='color:#388e3c'><b>➡️ Folgefrage:</b><br>{followup}</div>", unsafe_allow_html=True)

# ------ STAGE 5: Chat & Correction ------

if st.session_state["step"] == 5:
    # --- Setup daily usage tracking ---
    today_str    = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key    = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    st.info(
        f"Student code: `{student_code}` | "
        f"Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}"
    )

    # --- Determine special B1 Teil 3 mode ---
    is_b1_teil3 = (
        st.session_state.get("selected_mode", "").startswith("Geführte") and
        st.session_state.get("selected_exam_level") == "B1" and
        st.session_state.get("selected_teil", "").startswith("Teil 3")
    )

    # --- Inject initial assistant prompt if needed ---
    if is_b1_teil3 and not st.session_state["messages"]:
        topic = random.choice(B1_TEIL2)
        st.session_state["current_b1_teil3_topic"] = topic
        init = (
            f"Ich habe gerade eine kurze Präsentation über **{topic}** gehalten.\n\n"
            "Deine Aufgabe jetzt:\n"
            "- Stelle mir **zwei Fragen** zu meiner Präsentation (auf Deutsch).\n"
            "- Gib mir **eine positive Rückmeldung** auf Deutsch.\n\n"
            "👉 Schreib deine zwei Fragen und ein Feedback jetzt unten auf!"
        )
        st.session_state["messages"].append({"role": "assistant", "content": init})

    elif not st.session_state["messages"]:
        if st.session_state["selected_mode"].startswith("Geführte"):
            prompt = st.session_state.get("initial_prompt")
            st.session_state["messages"].append({"role": "assistant", "content": prompt})
        else:
            topic = st.session_state.get("custom_topic", "")
            if topic:
                st.session_state["messages"].append({"role": "user", "content": topic})
                try:
                    client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                    resp = client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[{"role":"system","content":ai_system_prompt}, *st.session_state["messages"]],
                    )
                    reply = resp.choices[0].message.content
                except Exception as e:
                    reply = "Sorry, there was a problem generating a response."
                    st.error(str(e))
                st.session_state["messages"].append({"role": "assistant", "content": reply})

    # --- Student input (audio upload or text) ---
    uploaded = st.file_uploader(
        "Upload an audio file (WAV, MP3, OGG, M4A)",
        type=["wav","mp3","ogg","m4a"],
        key="stage5_audio_upload"
    )
    typed = st.chat_input("💬 Oder tippe deine Antwort hier...", key="stage5_typed_input")
    user_input = None

    if uploaded:
        uploaded.seek(0)
        data = uploaded.read()
        st.audio(data, format=uploaded.type)
        try:
            suffix = "." + uploaded.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(data); tmp.flush()
            client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=open(tmp.name,"rb")
            )
            user_input = transcript.text
        except:
            st.warning("Transcription failed; please type your message.")
    elif typed:
        user_input = typed

    session_ended    = st.session_state["turn_count"] >= max_turns
    used_today       = st.session_state["daily_usage"][usage_key]
    ai_just_replied  = False

    # --- Process AI response ---
    if user_input and not session_ended:
        if used_today >= DAILY_LIMIT:
            st.warning(
                "You’ve reached today’s free practice limit. "
                "Please come back tomorrow or contact your tutor!"
            )
        else:
            st.session_state["messages"].append({"role":"user","content":user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1

            conversation = [
                {"role":"system","content":ai_system_prompt},
                st.session_state["messages"][-1]
            ]
            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp   = client.chat.completions.create(
                    model="gpt-3.5-turbo", messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))

            st.session_state["messages"].append(
                {"role":"assistant","content":ai_reply}
            )
            ai_just_replied = True

    # --- Render chat history with formatted AI replies ---
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                show_formatted_ai_reply(msg["content"])
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- Navigation buttons (single instance) ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
            st.session_state.update({"step":prev, "messages":[], "turn_count":0})
    with col2:
        if session_ended and st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6


# STAGE 6: Session Summary & Restart

if st.session_state["step"] == 6:
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
