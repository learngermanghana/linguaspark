import streamlit as st
from openai import OpenAI
import random
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av

# --- Secure API key ---
api_key = st.secrets.get("general", {}).get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()
client = OpenAI(api_key=api_key)

# --- Page setup ---
st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit header/styling
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Speech recognition helper ---
def recognize_speech(audio_bytes, language="en-US"):
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(audio_bytes, sample_rate=44100, sample_width=2)
    try:
        return recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand your speech."
    except sr.RequestError:
        return "Couldn't request results. Check your internet."

# --- UI components ---
st.title("🧑‍🏫 Falowen – Your AI Conversation Partner")

# Language selection
target_language = st.selectbox(
    "🌐 Choose your language",
    ["German", "English", "French", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic"]
)
language_codes = {
    "German": "de-DE", "English": "en-US", "French": "fr-FR", "Spanish": "es-ES",
    "Italian": "it-IT", "Portuguese": "pt-PT", "Chinese": "zh-CN", "Arabic": "ar-SA"
}

# --- Goethe Exam Preparation ---
st.sidebar.header("📚 Goethe Exam Prep")
level = st.sidebar.selectbox("Select Level", ["A1", "A2", "B1"])

# --- A1 Module ---
if level == "A1":
    exam_section = st.radio("Teil", ["Teil 1: Self-introduction", "Teil 2: Thema & Keyword", "Teil 3: Bitten"])

    if exam_section == "Teil 1: Self-introduction":
        st.header("👋 A1 Teil 1 – Self-introduction")
        fields = ["Name", "Alter", "Land", "Wohnort", "Sprachen", "Beruf", "Hobby"]
        answers = {}
        for field in fields:
            answers[field] = st.text_input(f"{field}:")
        if st.button("✅ Check Self-introduction"):
            intro = (
                f"Ich heiße {answers['Name']}. Ich bin {answers['Alter']} Jahre alt. "
                f"Ich komme aus {answers['Land']}. Ich wohne in {answers['Wohnort']}. "
                f"Ich spreche {answers['Sprachen']}. Ich arbeite als {answers['Beruf']}. "
                f"Mein Hobby ist {answers['Hobby']}."
            )
            st.success(intro)
            prompt = f"Correct this A1-level introduction for grammar and simplicity:\n{intro}"
            resp = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role":"system","content":prompt}],
                max_tokens=150
            )
            st.info(f"📝 Correction:\n{resp.choices[0].message.content.strip()}")

    elif exam_section == "Teil 2: Thema & Keyword":
        st.header("🗣️ A1 Teil 2 – Thema & Keyword")
        vocab = [
            ("Geschäft","schließen"),("Uhr","Uhrzeit"),("Arbeit","Kollege"),("Hausaufgabe","machen"),
            ("Küche","kochen"),("Freizeit","lesen"),("Telefon","anrufen"),("Reise","Hotel"),
            ("Auto","fahren"),("Einkaufen","Obst"),("Schule","Lehrer"),("Geburtstag","Geschenk"),
            ("Essen","Frühstück"),("Arzt","Termin"),("Zug","Abfahrt"),("Wetter","Regen"),
            ("Buch","lesen"),("Computer","E-Mail"),("Kind","spielen"),("Wochenende","Plan"),
            ("Bank","Geld"),("Sport","laufen"),("Abend","Fernsehen"),("Freunde","Besuch"),
            ("Bahn","Fahrkarte"),("Straße","Stau"),("Essen gehen","Restaurant"),("Hund","Futter"),
            ("Familie","Kinder"),("Post","Brief"),("Nachbarn","laut"),("Kleid","kaufen"),
            ("Büro","Chef"),("Urlaub","Strand"),("Kino","Film"),("Internet","Seite"),
            ("Bus","Abfahrt"),("Arztpraxis","Wartezeit"),("Kuchen","backen"),("Park","spazieren"),
            ("Bäckerei","Brötchen"),("Geldautomat","Karte"),("Buchladen","Roman"),("Fernseher","Programm"),
            ("Tasche","vergessen"),("Stadtplan","finden"),("Ticket","bezahlen"),("Zahnarzt","Schmerzen"),
            ("Museum","Öffnungszeiten"),("Handy","Akku leer")
        ]
        thema, keyword = random.choice(vocab)
        st.info(f"Thema: **{thema}**, Keyword: **{keyword}**")
        st.markdown("**Form your question or sentence using the Thema and Keyword.**")
        sentence = st.text_input("Ihre Frage/Satz:")
        if st.button("✅ Check Sentence"):
            if not sentence.strip(): st.warning("Bitte eingeben.")
            else:
                p = f"You are a German A1 teacher. Correct this sentence for correctness and simplicity:\n{sentence}"
                r = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{"role":"system","content":p}],
                    max_tokens=120
                )
                st.success(f"📝 Correction:\n{r.choices[0].message.content.strip()}")

    else:
        st.header("🙏 A1 Teil 3 – Bitten (Requests)")
        prompts = [
            "Radio anmachen","Fenster zumachen","Licht anschalten","Tür aufmachen","Tisch sauber machen",
            "Hausaufgaben schicken","Buch bringen","Handy ausmachen","Stuhl nehmen","Wasser holen",
            "Fenster öffnen","Musik leiser machen","Tafel sauber wischen","Kaffee kochen","Deutsch üben",
            "Auto waschen","Kind abholen","Tisch decken","Termin machen","Nachricht schreiben"
        ]
        req = random.choice(prompts)
        st.info(f"Prompt: **{req}**")
        st.markdown("**Make a polite request using 'bitte' or a modal verb.**")
        req_text = st.text_input("Ihre Bitte:")
        if st.button("✅ Check Request"):
            if not req_text.strip(): st.warning("Bitte eingeben.")
            else:
                p = f"You are a German A1 teacher. Correct and simplify this request:\n{req_text}"
                r = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{"role":"system","content":p}],
                    max_tokens=120
                )
                st.success(f"📝 Correction:\n{r.choices[0].message.content.strip()}")

# --- A2 Module ---
elif level == "A2":
    exam_section = st.radio("Teil", ["Teil 1: Introduction", "Teil 2: Presentation", "Teil 3: Planning"])

    if exam_section == "Teil 1: Introduction":
        st.header("👋 A2 Teil 1 – Introduction")
        name = st.text_input("Name:")
        alter = st.text_input("Alter:")
        wohnort = st.text_input("Wohnort:")
        beruf = st.text_input("Beruf:")
        hobby = st.text_input("Hobby:")
        if st.button("✅ Check Introduction"):
            intro = (
                f"Ich heiße {name}. Ich bin {alter} Jahre alt. "
                f"Ich wohne in {wohnort}. Ich arbeite als {beruf}. Mein Hobby ist {hobby}."
            )
            st.success(intro)
            prompt = f"Correct this A2-level introduction for grammar and phrasing:\n{intro}"
            resp = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role":"system","content":prompt}],
                max_tokens=150
            )
            st.info(f"📝 Correction:\n{resp.choices[0].message.content.strip()}")

    elif exam_section == "Teil 2: Presentation":
        st.header("🗣️ A2 Teil 2 – Short Presentation")
        topics = [
            "Mein letzter Urlaub","Meine Familie","Meine Wohnung","Mein Hobby",
            "Mein Lieblingsfilm","Mein Wochenende","Mein Lieblingsessen"
        ]
        chosen = random.choice(topics)
        st.info(f"Ihr Thema: **{chosen}**")
        st.markdown("**Bereiten Sie einen 1–2-minütigen Vortrag vor.**")
        pres = st.text_area("Ihre Präsentation:", height=180)
        if st.button("✅ Check Presentation"):
            if not pres.strip(): st.warning("Bitte Text eingeben.")
            else:
                gp = f"You are a German A2 teacher. Correct this presentation text:\n{pres}"
                r = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{"role":"system","content":gp}],
                    max_tokens=200
                )
                st.success(f"📝 Korrigiert:\n{r.choices[0].message.content.strip()}")

    else:
        st.header("🤝 A2 Teil 3 – Planning a Joint Activity")
        scenarios = [
            "Zusammen ins Kino gehen","Ein Café besuchen","Gemeinsam einkaufen gehen",
            "Ein Picknick im Park organisieren","Eine Fahrradtour planen","Zusammen in die Stadt gehen",
            "Einen Ausflug ins Schwimmbad machen","Eine Party organisieren",
            "Zusammen Abendessen gehen","Gemeinsam einen Freund besuchen","Zusammen ins Museum gehen"
        ]
        top = random.choice(scenarios)
        st.info(f"Planung: **{top}**")
        dia = st.text_area("Ihr Dialog:", height=180)
        if st.button("✅ Check Dialog"):
            if not dia.strip(): st.warning("Bitte Dialog eingeben.")
            else:
                p = f"You are a German A2 teacher. Correct this planning dialogue:\n{dia}"
                res = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{"role":"system","content":p}],
                    max_tokens=200
                )
                st.success(f"📝 Korrigiert:\n{res.choices[0].message.content.strip()}")

# --- B1 Module ---
elif level == "B1":
    st.header("🗣️ B1 Teil 2 – Long Turn Presentation")
    topics_b1 = [
        "Ausbildung","Auslandsaufenthalt","Behinderten-Sport","Berufstätige Eltern",
        "Berufswahl","Bio-Essen","Chatten","Computer für jeden Kursraum",
        "Das Internet","Einkaufen in Einkaufszentren","Einkaufen im Internet",
        "Extremsport","Facebook","Fertigessen","Freiwillige Arbeit",
        "Freundschaft","Gebrauchte Kleidung","Getrennter Unterricht für Jungen und Mädchen",
        "Haushalt","Haustiere","Heiraten","Hotel Mama","Ich bin reich genug",
        "Informationen im Internet","Kinder und Fernsehen","Kinder und Handys",
        "Kinos sterben","Kreditkarten","Leben auf dem Land oder in der Stadt",
        "Makeup für Kinder","Marken-Kleidung","Mode","Musikinstrument lernen",
        "Musik im Zeitalter des Internets","Rauchen","Reisen","Schokolade macht glücklich",
        "Sport treiben","Sprachenlernen","Sprachenlernen mit dem Internet",
        "Stadtzentrum ohne Autos","Studenten und Arbeit in den Ferien","Studium","Tattoos",
        "Teilzeitarbeit","Unsere Idole","Umweltschutz","Vegetarische Ernährung",
        "Zeitungslesen"
    ]
    topic = random.choice(topics_b1)
    st.info(f"Thema: **{topic}**")
    st.markdown("**Halten Sie einen 2–3-minütigen Vortrag zu diesem Thema.**")
    speech = st.text_area("Ihr Vortragstext:", height=200)
    if st.button("✅ Check B1 Presentation"):
        if not speech.strip(): st.warning("Bitte Vortrag eingeben.")
        else:
            gp2 = f"You are a German B1 teacher. Correct this presentation text:\n{speech}"
            r2 = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role":"system","content":gp2}],
                max_tokens=250
            )
            st.success(f"📝 Korrigiert:\n{r2.choices[0].message.content.strip()}")

st.caption("🔖 Ensure microphone permissions are enabled for speaking features.")
