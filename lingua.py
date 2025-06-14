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

# ---- Falowen / Herr Felix Header ----
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

# File/database constants
CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
max_turns = 15
TEACHER_PASSWORD = "Felix029"
USAGE_LOG_FILE = "usage_log.csv"

# Usage logging function
def log_usage(code):
    today = str(date.today())
    if os.path.exists(USAGE_LOG_FILE):
        df = pd.read_csv(USAGE_LOG_FILE)
    else:
        df = pd.DataFrame(columns=["code", "date", "count"])

    match = (df["code"] == code) & (df["date"] == today)
    if df[match].empty:
        df = pd.concat([df, pd.DataFrame({"code": [code], "date": [today], "count": [1]})], ignore_index=True)
    else:
        df.loc[match, "count"] += 1

    df.to_csv(USAGE_LOG_FILE, index=False)


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

    # --- REMOVE the custom_topic input! ---

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


# ------ STAGE 4: Exam Part Selection ------
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

def show_formatted_ai_reply(ai_reply):
    corr_pat = r'(?:-?\s*Correction:)\s*(.*?)(?=\n-?\s*Grammatik-Tipp:|\Z)'
    gram_pat = r'(?:-?\s*Grammatik-Tipp:)\s*(.*?)(?=\n-?\s*(?:Follow-up question|Folgefrage)|\Z)'
    foll_pat = r'(?:-?\s*(?:Follow-up question|Folgefrage):?)\s*(.*)'

    import re
    correction = re.search(corr_pat, ai_reply, re.DOTALL)
    grammatik  = re.search(gram_pat, ai_reply, re.DOTALL)
    followup   = re.search(foll_pat, ai_reply, re.DOTALL)

    main = ai_reply
    if correction:
        main = ai_reply.split(correction.group(0))[0].strip()

    st.markdown(f"**📝 Antwort:**  \n{main}", unsafe_allow_html=True)
    if correction:
        text = correction.group(1).strip()
        st.markdown(f"<div style='color:#c62828'><b>✏️ Korrektur:</b>  \n{text}</div>", unsafe_allow_html=True)
    if grammatik:
        text = grammatik.group(1).strip()
        st.markdown(f"<div style='color:#1565c0'><b>📚 Grammatik-Tipp:</b>  \n{text}</div>", unsafe_allow_html=True)
    if followup:
        text = followup.group(1).strip()
        st.markdown(f"<div style='color:#388e3c'><b>➡️ Folgefrage:</b>  \n{text}</div>", unsafe_allow_html=True)

# ------ STAGE 5 Logic ------
if st.session_state["step"] == 5:
    today_str    = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key    = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state.setdefault("a2_keyword_progress", set())
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    st.info(
    f"Student code: `{student_code}` | Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT} | "
    f"Turns used: {st.session_state['turn_count']}/{max_turns}"
)

# Progress Bar
if st.session_state.get("custom_chat_level") == "A2" and st.session_state.get("a2_keywords"):
    total_keywords = len(st.session_state["a2_keywords"])
    completed_keywords = len(st.session_state["a2_keyword_progress"])
    st.progress(completed_keywords / total_keywords)
    st.markdown("**Progress:** " + " | ".join([
        f"✅ `{kw}`" if kw in st.session_state["a2_keyword_progress"] else f"⬜ `{kw}`"
        for kw in st.session_state["a2_keywords"]
    ]))
else:
    st.progress(st.session_state['turn_count'] / max_turns)

    is_b1_teil3 = (
        st.session_state.get("selected_mode", "").startswith("Geführte") and
        st.session_state.get("selected_exam_level") == "B1" and
        st.session_state.get("selected_teil", "").startswith("Teil 3")
    )

    if st.session_state.get("custom_chat_level") == "A2" and st.session_state.get("a2_keywords"):
        st.subheader("📊 Presentation Keyword Progress")
        completed = st.session_state["a2_keyword_progress"]
        total = set(st.session_state["a2_keywords"])
        remaining = total - completed

        st.markdown("**Completed:** " + ", ".join([f"✅ `{kw}`" for kw in completed]) if completed else "**Completed:** -")
        st.markdown("**Remaining:** " + ", ".join([f"🕓 `{kw}`" for kw in remaining]) if remaining else "**Remaining:** 🎉 All keywords completed!")

        if not remaining:
            st.success("🎉 Great job! You've covered all your keywords. Now let's build your final presentation!")
            if st.button("🧩 Build My Final Presentation"):
                all_sentences = []
                for msg in st.session_state["messages"]:
                    if msg["role"] == "user":
                        all_sentences.append(f"👤 {msg['content']}")
                    elif msg["role"] == "assistant":
                        all_sentences.append(f"🧑‍🏫 {msg['content']}")
                final_presentation = "\n\n".join(all_sentences)
                st.markdown("---")
                st.subheader("📄 Your Final Presentation")
                st.markdown(final_presentation)

                import io
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in final_presentation.split("\n"):
                    pdf.multi_cell(0, 10, line)
                pdf_output = io.BytesIO()
                pdf.output(pdf_output)
                st.download_button("📥 Download My Practice (PDF)", data=pdf_output.getvalue(), file_name="A2_Presentation_Practice.pdf")

        if st.session_state.get("messages") and st.session_state["messages"][-1]["role"] == "user":
            latest_input = st.session_state["messages"][-1]["content"].lower()
            for kw in st.session_state["a2_keywords"]:
                if kw.lower() in latest_input:
                    st.session_state["a2_keyword_progress"].add(kw)

    if (
        st.session_state.get("selected_mode", "") == "Eigenes Thema/Frage (Custom Topic Chat)"
        and not st.session_state.get("custom_chat_level")
    ):
        level = st.radio(
            "Wähle dein Sprachniveau / Select your level:",
            ["A2", "B1"],
            horizontal=True,
            key="custom_level_select"
        )
        if st.button("Start Custom Chat"):
            st.session_state["custom_chat_level"] = level
            st.session_state["a2_keywords"] = None
            st.session_state["custom_topic_acknowledged"] = False
            st.session_state["a2_keyword_progress"] = set()
            st.session_state["messages"] = [{
                "role": "assistant",
                "content": (
                    "🎤 **Presentation Practice – A2 Level**\n\n"
                    "Please write one short sentence to tell me your presentation topic. ✍️\n\n"
                    "**Examples:**\n"
                    "- Ich möchte über meine Familie sprechen.\n"
                    "- Ich will über mein Lieblingsessen sprechen.\n"
                    "- I want to talk about my school.\n\n"
                    "💡 *Then I will help you step by step — first, I’ll ask for 3–4 keywords, then we’ll build your presentation together!*"
                )
            }]
        st.stop()

    uploaded = st.file_uploader("Upload an audio file (WAV, MP3, OGG, M4A)", type=["wav", "mp3", "ogg", "m4a"])
    typed = st.chat_input("💬 Or type your message here...")
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
                model="whisper-1", file=open(tmp.name, "rb")
            )
            user_input = transcript.text
        except:
            st.warning("Transcription failed; please type your message.")
    elif typed:
        user_input = typed

    session_ended = st.session_state["turn_count"] >= max_turns
    if user_input and not session_ended:
        if st.session_state["daily_usage"][usage_key] >= DAILY_LIMIT:
            st.warning("You’ve reached today’s free practice limit. Please come back tomorrow or contact your tutor!")
        else:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1
            log_usage(student_code)

            import re
            user_words = re.findall(r"\b[a-zäöüß]+\b", user_input.lower())

            if st.session_state["selected_mode"] == "Eigenes Thema/Frage (Custom Topic Chat)" and st.session_state["custom_chat_level"] == "A2":
                if not st.session_state.get("a2_keywords") and len(user_words) >= 3:
                    st.session_state["a2_keywords"] = user_words[:4]
                    st.success(f"✅ Thanks! I've added these keywords to your presentation: {', '.join(st.session_state['a2_keywords'])}")

                if not st.session_state.get("a2_keywords"):
                    ai_system_prompt = (
                        "You are Herr Felix, an A2-level German teacher. The student gave a topic but not their 3–4 German keywords yet."
                        " Ask once in English with examples like 'Eltern, Bruder, Wochenende'."
                        " Do not repeat this request if they already gave them."
                    )
                elif not st.session_state.get("custom_topic_acknowledged"):
                    st.session_state["custom_topic_acknowledged"] = True
                    keywords = st.session_state["a2_keywords"]
                    highlighted = ", ".join([f"**{kw}**" for kw in keywords])
                    ai_system_prompt = (
                        f"You are Herr Felix, an A2-level German teacher helping a student prepare a presentation."
                        f" Use the keywords: {highlighted} to give initial ideas."
                        " Provide idea suggestions (in English), with German examples. Also give one sentence starter (German), one correction (German), one grammar tip (English), and one follow-up question (German)."
                    )
                else:
                    keywords = st.session_state["a2_keywords"]
                    highlighted = ", ".join([f"**{kw}**" for kw in keywords])
                    ai_system_prompt = (
                        f"You are Herr Felix, an A2-level teacher. The student has already chosen a topic and keywords: {highlighted}."
                        " Now continue the conversation in a natural way using these keywords."
                        " Each response should focus on one keyword or question. Give one correction and one follow-up question only."
                    )
            else:
                ai_system_prompt = "You are Herr Felix. Just reply in German."

            conversation = [
                {"role": "system", "content": ai_system_prompt},
                st.session_state["messages"][-1]
            ]

            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))

            st.session_state["messages"].append({"role": "assistant", "content": ai_reply})

    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown("<span style='color:#33691e;font-weight:bold'>🧑‍🏫 Herr Felix:</span>", unsafe_allow_html=True)
                import re
                reply_text = msg["content"]
                reply_text = re.sub(r"(?i)\*\*Ideenvorschl[äa]ge:?\*\*", "\n\n🔹 **Idea Suggestions (in English):**", reply_text)
                reply_text = re.sub(r"(?i)\*\*Satzanfang:?\*\*", "\n\n🔹 **Sentence Starter:**", reply_text)
                reply_text = re.sub(r"(?i)\*\*Korrektur:?\*\*", "\n\n✏️ **Correction:**", reply_text)
                reply_text = re.sub(r"(?i)\*\*Grammatiktipp:?\*\*", "\n\n📘 **Grammar Tip (English Explanation):**", reply_text)
                reply_text = re.sub(r"(?i)\*\*Folgefrage:?\*\*", "\n\n➡️ **Next Question (in German):**", reply_text)
                show_formatted_ai_reply(reply_text)
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            prev = 4 if st.session_state["selected_mode"].startswith("Geführte") else 3
            st.session_state.update({
                "step": prev,
                "messages": [],
                "turn_count": 0,
                "custom_chat_level": None,
                "a2_keywords": None,
                "a2_keyword_progress": set()
            })
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
            # Reset based on the previous mode
            if st.session_state.get("selected_mode") == "Geführte Prüfungssimulation (Exam Mode)":
                st.session_state["step"] = 4  # Restart from exam part selection
            else:
                st.session_state["step"] = 5  # Continue in Custom Chat mode

            # Clear session state
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["custom_topic"] = ""
            st.session_state["initial_prompt"] = ""
            st.session_state["custom_chat_level"] = None
            st.session_state["selected_exam_level"] = ""
            st.session_state["selected_teil"] = ""

    with col2:
        if st.button("⬅️ Back to Mode Selection", key="stage6_back"):
            st.session_state["step"] = 3
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
    with col2:
        if st.button("⬅️ Back to Mode Selection", key="stage6_back"):
            st.session_state["step"] = 3
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
