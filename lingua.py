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
    page_title="Falowen – Dein KI-Sprachpartner (Deutsch)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit header/styling
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Daily Tip ---
daily_tips = [
    "💡 Tipp: Übe jeden Tag 5 neue Wörter.",
    "💡 Tipp: Wiederhole laut, um die Aussprache zu verbessern.",
    "💡 Tipp: Schreibe kurze Sätze und bitte Sir Felix um Korrektur.",
    "💡 Tipp: Höre einfache deutsche Podcasts für 5 Minuten.",
    "💡 Tipp: Sprich mit dir selbst, um flüssiger zu werden."
]
st.info(random.choice(daily_tips))

# --- Initialize chat state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Speech recognition helper ---
def recognize_speech(audio_bytes, language="de-DE"):
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(audio_bytes, sample_rate=44100, sample_width=2)
    try:
        return recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand your speech."
    except sr.RequestError:
        return "Couldn't request results. Check your internet."

# --- UI components ---
st.title("🧑‍🏫 Falowen – Dein KI-Sprachpartner (Deutsch)")

# --- Chat Interface ---
st.subheader("💬 Chat mit Sir Felix")
for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.chat_message("user").markdown(msg['content'])
    else:
        st.chat_message("assistant", avatar="🧑‍🏫").markdown(msg['content'])

user_input = st.chat_input("Schreibe hier deine Nachricht...")
if user_input:
    st.session_state.messages.append({'role': 'user', 'content': user_input})
    st.chat_message("user").markdown(user_input)
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'system', 'content': 'Du bist Sir Felix, ein freundlicher Deutschlehrer. Ermutige Schüler und erkläre einfach.'}, *st.session_state.messages]
    )
    ai_reply = response.choices[0].message.content
    st.session_state.messages.append({'role': 'assistant', 'content': ai_reply})
    st.chat_message("assistant", avatar="🧑‍🏫").markdown(ai_reply)

# --- Sidebar: Exam Preparation ---
st.sidebar.header("📚 Goethe Prüfen (Deutsch)")
level = st.sidebar.selectbox("Wähle Niveau", ["A1", "A2", "B1"])  

# --- A1 Module ---
if level == "A1":
    section = st.sidebar.radio("Teil auswählen", ["Teil 1: Vorstellung", "Teil 2: Thema & Keyword", "Teil 3: Bitten"])
    if section == "Teil 1: Vorstellung":
        st.header("👋 A1 Teil 1 – Vorstellung")
        name = st.text_input("Name:")
        alter = st.text_input("Alter:")
        ort = st.text_input("Wohnort:")
        if st.button("✅ Überprüfen der Vorstellung"):
            text = f"Ich heiße {name}. Ich bin {alter} Jahre alt. Ich wohne in {ort}."
            st.success(text)
            prompt = f"Korrigiere diesen A1-Vorstellungstext:\n{text}"
            res = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{"role":"system","content":prompt}], max_tokens=100)
            st.info(res.choices[0].message.content.strip())
    elif section == "Teil 2: Thema & Keyword":
        st.header("🗣️ A1 Teil 2 – Thema & Keyword")
        vocab = [("Geschäft","schließen"),("Uhr","Uhrzeit"),("Arbeit","Kollege"),("Hausaufgabe","machen"),("Küche","kochen"),("Freizeit","lesen"),("Telefon","anrufen"),("Reise","Hotel"),("Auto","fahren"),("Einkaufen","Obst")]
        thema, keyw = random.choice(vocab)
        st.info(f"Thema: **{thema}**, Keyword: **{keyw}**")
        sentence = st.text_input("Dein Satz:")
        if st.button("✅ Satz prüfen"):
            prompt = f"Korrigiere diesen A1-Satz:\n{sentence}"
            res = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{"role":"system","content":prompt}], max_tokens=100)
            st.success(res.choices[0].message.content.strip())
    else:
        st.header("🙏 A1 Teil 3 – Bitten")
        prompts = ["Radio anmachen","Fenster zummachen","Licht anschalten"]
        req = random.choice(prompts)
        st.info(f"Prompt: **{req}**")
        req_text = st.text_input("Deine Bitte:")
        if st.button("✅ Bitte prüfen"):
            prompt = f"Korrigiere diese A1-Bitte:\n{req_text}"
            res = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{"role":"system","content":prompt}], max_tokens=100)
            st.success(res.choices[0].message.content.strip())
# --- A2 Module ---
elif level == "A2":
    section = st.sidebar.radio("Teil auswählen", ["Teil 1: Vorstellung", "Teil 2: Präsentation", "Teil 3: Planung"])
    if section == "Teil 2: Präsentation":
        st.header("🗣️ A2 Teil 2 – Präsentation")
        topics = ["Mein letzter Urlaub","Meine Familie"]
        top = random.choice(topics)
        st.info(f"Thema: **{top}**")
        pres = st.text_area("Deine Präsentation:")
        if st.button("✅ Präsentation prüfen"):
            prompt = f"Korrigiere diese A2-Präsentation:\n{pres}"
            res = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{"role":"system","content":prompt}], max_tokens=150)
            st.success(res.choices[0].message.content.strip())
# --- B1 Module ---
elif level == "B1":
    st.header("🗣️ B1 Teil 2 – Präsentation")
    topics_b1 = ["Ausbildung","Freundschaft","Umweltschutz"]
    tb = random.choice(topics_b1)
    st.info(f"Thema: **{tb}**")
    speech = st.text_area("Deine Präsentation:")
    if st.button("✅ Prüfung"):
        prompt = f"Korrigiere diese B1-Präsentation:\n{speech}"
        res = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{"role":"system","content":prompt}], max_tokens=200)
        st.success(res.choices[0].message.content.strip())
st.caption("🔖 Mikrofonberechtigung für Sprechen aktivieren.")
