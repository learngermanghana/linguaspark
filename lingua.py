import streamlit as st
from openai import OpenAI
from datetime import datetime
import pandas as pd
import uuid
import tempfile
import io
from gtts import gTTS
import random

st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .st-emotion, .st-emotion-actions, .st-emotion-cache {visibility: hidden !important;}
    .stChatMessage.user {background: #e1f5fe; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    .stChatMessage.assistant {background: #f0f4c3; border-radius: 12px; margin-bottom: 5px; padding: 8px;}
    </style>
""", unsafe_allow_html=True)

# --- Random Fun Fact ---
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

# --- Main App Header ---
st.markdown(
    "<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor, Herr Felix!</h2>",
    unsafe_allow_html=True,
)
st.markdown("> Practice your speaking or writing. Get simple AI feedback and audio answers!")

# === Motivational Exam Bootcamp ===
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

# === Expander with Exam Info and PDFs ===
with st.expander("🎤 German Speaking Exam – A2 & B1: Format, Tips, and Practice Topics (click to expand)"):
    st.markdown("""
    ### 🗣️ **A2 Sprechen (Goethe-Zertifikat) – Structure**
    **Teil 1:** Fragen zu Schlüsselwörtern (Questions based on key words)
    - Wohnort, Beruf, Geburtstag, Hobby, Familie, Reisen, Lieblingsessen, Wetter, etc.

    **Teil 2:** Bildbeschreibung & Diskussion (Picture description & discussion)
    - Example: *Was machen Sie mit Ihrem Geld?* – Kleidung, Reisen, sparen...

    **Teil 3:** Gemeinsam planen (Planning together)
    - E.g., Kino, Picknick, Party, Freund besuchen.

    ---
    ### 🗣️ **B1 Sprechen (Goethe-Zertifikat) – Structure**
    **Teil 1:** Planning together (Dialogue)
    **Teil 2:** Individual Presentation
    **Teil 3:** Give feedback and ask questions

    ---
    **Download full topic sheets for practice:**  
    [A2 Sprechen Topic Sheet (PDF)](sandbox:/mnt/data/A2%20sprechen.pdf)  
    [B1 Sprechen Topic Sheet (PDF)](sandbox:/mnt/data/Sprechen%20B1%20(Goethe%20Exams).pdf)
    """)
    
# === Random Exam Topic Trainer ===
a2_topics = [
    "Wohnort", "Tagesablauf", "Freizeit", "Sprachen", "Essen & Trinken", "Haustiere",
    "Lieblingsmonat", "Jahreszeit", "Sport", "Kleidung (Sommer)", "Familie", "Beruf",
    "Hobbys", "Feiertage", "Reisen", "Lieblingsessen", "Schule", "Wetter", "Auto oder Fahrrad", "Perfekter Tag"
]
b1_topics = [
    "Ausbildung", "Berufswahl", "Bio-Essen", "Chatten", "Einkaufen", "Facebook",
    "Freiwillige Arbeit", "Haustiere", "Heiraten", "Leben auf dem Land oder in der Stadt",
    "Mode", "Musikinstrument lernen", "Reisen", "Sport treiben", "Umweltschutz",
    "Vegetarische Ernährung", "Zeitungslesen"
]

st.markdown("---")
st.markdown("## 🎲 **Train Like the Real Exam!**")
exam_level = st.selectbox("Choose exam level for random topic:", ["A2 Sprechen", "B1 Sprechen"], key="exam_level")
if exam_level == "A2 Sprechen":
    if st.button("🎤 Give me a random A2 topic!", key="random_a2"):
        topic = random.choice(a2_topics)
        st.success(f"📝 **Your A2 Sprechen exam topic:**\n\n`{topic}`\n\nImagine you're in the exam! Ask and answer questions about this topic for 1–2 minutes.")
elif exam_level == "B1 Sprechen":
    if st.button("🎤 Give me a random B1 topic!", key="random_b1"):
        topic = random.choice(b1_topics)
        st.success(f"📝 **Your B1 Sprechen exam topic:**\n\n`{topic}`\n\nImagine you're in the exam! Give a short presentation (intro, experience, pros/cons, conclusion).")

st.caption("Keep clicking for more surprise exam-style topics. Every practice session makes you more confident for the real day!")

# ========== Chat/Practice Logic ==========
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

# -- Language + Level selection (optional) --
language = st.selectbox("🌍 Choose your language", 
    ["German", "French", "English", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic"]
)
level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"], key="level")

# -- User input (chat or audio) --
uploaded_audio = st.file_uploader("Upload an audio file (WAV, MP3, OGG, M4A)", type=["wav", "mp3", "ogg", "m4a"], key="audio_upload")
typed_message = st.chat_input("💬 Or type your message here...", key="typed_input")

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

if user_input:
    st.session_state['messages'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(f"🗣️ {user_input}")

    try:
        ai_system_prompt = (
            f"You are Herr Felix, a friendly {language} tutor. "
            f"Always answer in exam mood for level {level} unless told otherwise."
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
        try:
            lang_codes = {
                "German": "de",
                "French": "fr",
                "Spanish": "es",
                "Italian": "it",
                "Portuguese": "pt",
                "Chinese": "zh-CN",
                "Arabic": "ar",
                "English": "en"
            }
            tts_lang = lang_codes.get(language, "en")
            tts = gTTS(ai_reply, lang=tts_lang)
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

# --- WhatsApp Share Button ---
share_text = "I just practiced my language skills with Herr Felix on Falowen! 🌟 Try it too: https://falowen.streamlit.app"
share_url = f"https://wa.me/?text={share_text.replace(' ', '%20')}"
st.markdown(
    f'<a href="{share_url}" target="_blank">'
    '<button style="background:#25D366;color:white;padding:7px 14px;border:none;border-radius:6px;margin-top:10px;font-size:1em;">'
    'Share on WhatsApp 🚀</button></a>',
    unsafe_allow_html=True
)
