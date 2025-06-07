import streamlit as st
from openai import OpenAI
import tempfile
import io
from gtts import gTTS
import random
import re
import pandas as pd
import os
from datetime import date

TEACHER_PASSWORD = "Felix029"  

st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ======= CODE MANAGEMENT FUNCTIONS =======
CODES_FILE = "student_codes(1).csv"

def load_codes():
    if os.path.exists(CODES_FILE):
        df = pd.read_csv(CODES_FILE)
        if "code" not in df.columns:
            df = pd.DataFrame(columns=["code"])
    else:
        df = pd.DataFrame(columns=["code"])
    return df

def save_codes(df):
    df.to_csv(CODES_FILE, index=False)

# ======= TABS: PRACTICE & TEACHER DASHBOARD =======
tab1, tab2 = st.tabs(["Practice", "Teacher Dashboard"])

with tab1:
    # ========== STUDENT CODE LOGIN & USAGE LIMIT ==========
    df_codes = load_codes()
    if "student_code" not in st.session_state:
        st.session_state["student_code"] = ""

    if not st.session_state["student_code"]:
        code = st.text_input("🔑 Enter your student code to begin:", key="code_entry")
        if code:
            code = code.strip().lower()
            if code in df_codes["code"].values:
                st.session_state["student_code"] = code
                st.rerun()
            else:
                st.error("This code is not recognized. Please check with your tutor.")
        st.stop()

    student_code = st.session_state["student_code"]

    if "daily_usage" not in st.session_state:
        st.session_state["daily_usage"] = {}

    today_str = str(date.today())
    usage_key = f"{student_code}_{today_str}"
    if usage_key not in st.session_state["daily_usage"]:
        st.session_state["daily_usage"][usage_key] = 0

    DAILY_LIMIT = 10

    col1, col2 = st.columns([4, 1])
    col1.info(f"Student code: `{student_code}`  |  Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}")
    if col2.button("Log out"):
        for key in ["student_code", "messages", "corrections", "turn_count"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

    # --- Fun Fact & Header ---
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
    random_fact = random.choice(fun_facts)
    st.success(f"**Did you know?** {random_fact}")

    st.markdown(
        "<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor, Herr Felix!</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("> Practice your German speaking or writing. Get simple AI feedback and audio answers!")

    st.info(
        """
        🎤 **This is not just chat—it's your personal exam preparation bootcamp!**
        Every time you talk to Herr Felix, imagine you are **in the exam hall**.
        Expect realistic A2 and B1 speaking questions, surprise prompts, and real exam tips.
        Sometimes, you’ll even get questions from last year’s exam!
        Let’s make exam training engaging, surprising, and impactful.  
        **Are you ready? Let’s go! 🚀**
        """, icon="💡"
    )

    with st.expander("🎤 German Speaking Exam – A2 & B1: Format, Tips, and Practice Topics (click to expand)"):
        st.markdown("""
        ### 🗣️ **A2 Sprechen (Goethe-Zertifikat) – Structure**
        **Teil 1:** Fragen zu Schlüsselwörtern  
        **Teil 2:** Bildbeschreibung & Diskussion  
        **Teil 3:** Gemeinsam planen  

        ---
        ### 🗣️ **B1 Sprechen (Goethe-Zertifikat) – Structure**
        **Teil 1:** Gemeinsam planen (Dialogue)  
        **Teil 2:** Präsentation (Monologue)  
        **Teil 3:** Feedback & Fragen stellen  

        ---
        **Download full topic sheets for practice:**  
        [A2 Sprechen Topic Sheet (PDF)](sandbox:/mnt/data/A2%20sprechen.pdf)  
        [B1 Sprechen Topic Sheet (PDF)](sandbox:/mnt/data/Sprechen%20B1%20(Goethe%20Exams).pdf)
        """)

    # ==== Official Exam Topics ====
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
        "Etwas überraschend finden", "Weitere Details erfragen"
    ]

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "transcript" not in st.session_state:
        st.session_state["transcript"] = ""
    if "corrections" not in st.session_state:
        st.session_state["corrections"] = []
    if "turn_count" not in st.session_state:
        st.session_state["turn_count"] = 0

    mode = st.radio(
        "Wie möchtest du üben?",
        ["Geführte Prüfungssimulation (Exam Mode)", "Eigenes Thema/Frage (Custom Topic Chat)"],
        index=0
    )

    max_turns = 6

    if mode == "Geführte Prüfungssimulation (Exam Mode)":
        exam_level = st.selectbox("Welches Prüfungsniveau möchtest du üben?", ["A2", "B1"], key="exam_level")
        if exam_level == "A2":
            teil_options = [
                "Teil 1 – Fragen zu Schlüsselwörtern",
                "Teil 2 – Bildbeschreibung & Diskussion",
                "Teil 3 – Gemeinsam planen"
            ]
        else:
            teil_options = [
                "Teil 1 – Gemeinsam planen (Dialogue)",
                "Teil 2 – Präsentation (Monologue)",
                "Teil 3 – Feedback & Fragen stellen"
            ]
        teil = st.selectbox("Welchen Teil möchtest du üben?", teil_options, key="teil")

        desc = ""
        if exam_level == "A2":
            if teil.startswith("Teil 1"):
                desc = "Du bekommst ein Schlüsselwort (wie 'Familie', 'Freizeit', 'Wohnort'). Stelle eine passende Frage und beantworte eine Frage dazu – auf Deutsch."
            elif teil.startswith("Teil 2"):
                desc = "Beschreibe eine Situation oder beantworte Fragen zu einem Alltagsthema (z.B. 'Was machen Sie am Wochenende?')."
            elif teil.startswith("Teil 3"):
                desc = "Plane mit deinem Partner etwas gemeinsam (z.B. einen Ausflug, Kino, Party). Mache Vorschläge, reagiere auf deinen Partner, und trefft eine Entscheidung."
        else:
            if teil.startswith("Teil 1"):
                desc = "Plane gemeinsam mit deinem Partner etwas (z.B. eine Reise, ein Fest). Mache Vorschläge, antworte, und treffe eine Entscheidung – alles auf Deutsch."
            elif teil.startswith("Teil 2"):
                desc = "Halte eine kurze Präsentation zu einem zufälligen Thema: Begrüße, nenne das Thema, gib deine Meinung, Vor- und Nachteile, und fasse zusammen. Alles auf B1-Niveau."
            elif teil.startswith("Teil 3"):
                desc = "Stelle nach der Präsentation deines Partners 1–2 Fragen und gib positives, konstruktives Feedback – auf Deutsch."
        st.info(f"**Was erwartet dich in {teil}?** {desc}")

        if st.button("Start Practice!"):
            st.session_state["messages"] = []
            st.session_state["corrections"] = []
            st.session_state["turn_count"] = 0
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
            st.session_state["messages"].append({"role": "assistant", "content": prompt})

        st.caption("Du kannst jederzeit einen neuen Teil wählen oder im Chat üben.")

    else:
        # ====== CUSTOM TOPIC CHAT ======
        custom_topic = st.text_input("Type your own topic or question here (e.g. from Google Classroom, homework, or any free conversation)...")
        if st.button("Start the conversation on my topic!"):
            st.session_state["messages"] = []
            st.session_state["corrections"] = []
            st.session_state["turn_count"] = 0
            if custom_topic.strip():
                st.session_state["messages"].append({
                    "role": "user",
                    "content": custom_topic.strip()
                })
        st.caption("You choose the topic – Herr Felix will help you, give tips, and correct your mistakes!")

    # -- User input (chat or audio) --
    uploaded_audio = st.file_uploader("Upload an audio file (WAV, MP3, OGG, M4A)", type=["wav", "mp3", "ogg", "m4a"], key="audio_upload")
    typed_message = st.chat_input("💬 Oder tippe deine Antwort hier...", key="typed_input")

    user_input = None
    if uploaded_audio is not None:
        uploaded_audio.seek(0)
        audio_bytes = uploaded_audio.read()
        st.audio(audio_bytes, format=uploaded_audio.type)
        st.download_button(
            label="⬇️ Download Your Uploaded Audio",
            data=audio_bytes,
            file_name=uploaded_audio.name,
            mime=uploaded_audio.type
        )
        try:
            suffix = "." + uploaded_audio.name.split(".")[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
            client = OpenAI(api_key=st.secrets.get("general", {}).get("OPENAI_API_KEY"))
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp.name, "rb")
            )
            user_input = transcript.text
        except Exception:
            st.warning("Transcription failed. Please try again or type your message.")
    else:
        if typed_message:
            user_input = typed_message

    # --- Chat display ---
    for msg in st.session_state['messages']:
        if msg['role'] == 'assistant':
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Herr Felix:</span> {msg['content']}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- Only accept messages while not at max turns and daily usage ---
    session_ended = st.session_state["turn_count"] >= max_turns
    used_today = st.session_state["daily_usage"][usage_key]
    if user_input and not session_ended:
        if used_today >= DAILY_LIMIT:
            st.warning("You’ve reached today’s free practice limit. Please come back tomorrow or contact your tutor for unlimited access!")
        else:
            st.session_state['messages'].append({'role': 'user', 'content': user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1

            try:
                if mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                    extra_end = (
                        "After 6 student answers, give a short, positive summary, "
                        "suggest a new topic or a break, and do NOT answer further unless restarted."
                        if st.session_state["turn_count"] >= max_turns else ""
                    )
                    ai_system_prompt = (
                        "You are Herr Felix, an expert German teacher and exam trainer. "
                        "Help the student have a conversation about their chosen topic, answer questions, correct mistakes, "
                        "and always give a short 'Grammatik-Tipp:' or suggestion after each reply. "
                        "Be friendly, explain in simple German when needed, and encourage the student to practice more. "
                        + extra_end
                    )
                else:
                    extra_end = (
                        "This is the end of the session. Give a positive summary, encourage a new topic or a break, and do NOT answer more unless the student restarts."
                        if st.session_state["turn_count"] >= max_turns else ""
                    )
                    ai_system_prompt = (
                        "You are Herr Felix, a highly intelligent, friendly, but strict Goethe-Prüfer (examiner) for German A2/B1. "
                        "Always answer as an examiner, then on a new line write 'Grammatik-Tipp: [correction/tip]' based on the student's last answer. "
                        + extra_end +
                        " Never break character."
                    )
                client = OpenAI(api_key=st.secrets.get("general", {}).get("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[
                        {'role': 'system', 'content': ai_system_prompt},
                        *st.session_state['messages']
                    ]
                )
                ai_reply = response.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response. Please try again."
                st.error(str(e))

            st.session_state['messages'].append({'role': 'assistant', 'content': ai_reply})
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"🧑‍🏫 <span style='color:#33691e;font-weight:bold'>Herr Felix:</span> {ai_reply}", unsafe_allow_html=True)
                # Extract and store grammar tip
                tip_match = re.search(r"Grammatik-Tipp\s*:\s*(.+)", ai_reply)
                if tip_match:
                    tip = tip_match.group(1).strip()
                    if tip and tip not in st.session_state["corrections"]:
                        st.session_state["corrections"].append(tip)
                try:
                    tts = gTTS(ai_reply, lang="de")
                    tts_bytes = io.BytesIO()
                    tts.write_to_fp(tts_bytes)
                    tts_bytes.seek(0)
                    tts_data = tts_bytes.read()
                    st.audio(tts_data, format="audio/mp3")
                    st.download_button(
                        label="⬇️ Download AI Response Audio",
                        data=tts_data,
                        file_name="response.mp3",
                        mime="audio/mp3"
                    )
                except Exception:
                    st.info("Audio feedback not available or an error occurred.")

    # --- Session ending and restart option ---
    if session_ended:
        st.success("🎉 **Session beendet!** Du hast fleißig geübt. Willst du ein neues Thema oder eine Pause?")
        if st.button("Neue Session starten"):
            st.session_state["messages"] = []
            st.session_state["corrections"] = []
            st.session_state["turn_count"] = 0

    # --- Show tracked grammar tips
    if st.session_state["corrections"]:
        st.markdown("### 📋 **Your Grammar Corrections & Tips so far**")
        for tip in st.session_state["corrections"]:
            st.write(f"- {tip}")

with tab2:
    st.header("👩‍🏫 Teacher Dashboard – Manage Student Codes")

    if "teacher_authenticated" not in st.session_state:
        st.session_state["teacher_authenticated"] = False

    if not st.session_state["teacher_authenticated"]:
        pwd = st.text_input("Teacher Password:", type="password", key="teacher_pwd")
        if st.button("Login", key="teacher_login_btn"):
            if pwd == TEACHER_PASSWORD:
                st.session_state["teacher_authenticated"] = True
                st.success("Access granted!")
                st.experimental_rerun()
            else:
                st.error("Incorrect password. Please try again.")
        st.stop()
    else:
        # Teacher Dashboard content as before:
        df_codes = load_codes()
        st.subheader("Current Codes")
        st.write(df_codes)

        new_code = st.text_input("Add a new student code")
        if st.button("Add Code"):
            new_code = new_code.strip().lower()
            if new_code and new_code not in df_codes["code"].values:
                df_codes = pd.concat([df_codes, pd.DataFrame({"code": [new_code]})], ignore_index=True)
                save_codes(df_codes)
                st.success(f"Code '{new_code}' added!")
                st.experimental_rerun()
            elif not new_code:
                st.warning("Enter a code to add.")
            else:
                st.warning("Code already exists.")

        remove_code = st.selectbox("Select code to remove", [""] + df_codes["code"].tolist())
        if st.button("Remove Selected Code"):
            if remove_code:
                df_codes = df_codes[df_codes["code"] != remove_code]
                save_codes(df_codes)
                st.success(f"Code '{remove_code}' removed!")
                st.experimental_rerun()
            else:
                st.warning("Choose a code to remove.")
        
        if st.button("Log out (Teacher)"):
            st.session_state["teacher_authenticated"] = False
            st.experimental_rerun()
