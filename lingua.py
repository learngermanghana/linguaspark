import streamlit as st
from openai import OpenAI
from datetime import datetime
import pandas as pd
import uuid
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

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- Speech recognition helper ---
def recognize_speech(audio_bytes, language="en-US"):
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(audio_bytes, sample_rate=44100, sample_width=2)
    try:
        text = recognizer.recognize_google(audio_data, language=language)
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand your speech."
    except sr.RequestError:
        return "Couldn't request results. Check your internet."

# --- UI components ---
st.title("🧑‍🏫 Falowen – Your AI Conversation Partner")

# Language selection
language = st.selectbox("🌐 Choose your language", ["German", "English", "French", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic"])
language_codes = {"German": "de-DE", "English": "en-US", "French": "fr-FR", "Spanish": "es-ES",
                  "Italian": "it-IT", "Portuguese": "pt-PT", "Chinese": "zh-CN", "Arabic": "ar-SA"}

# --- Chat Interface ---
for msg in st.session_state['messages']:
    role = "🧑‍🏫 Sir Felix" if msg['role'] == 'assistant' else "👤 You"
    st.markdown(f"**{role}:** {msg['content']}")

user_input = st.chat_input("💬 Type your message...")
if user_input:
    st.session_state['messages'].append({'role': 'user', 'content': user_input})

    # GPT Response
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': f"You are Sir Felix, a friendly {language} tutor."},
            *st.session_state['messages']
        ]
    )
    ai_reply = response.choices[0].message.content
    st.session_state['messages'].append({'role': 'assistant', 'content': ai_reply})

    # Display response
    st.markdown(f"🧑‍🏫 **Sir Felix:** {ai_reply}")

    # Grammar Check
    grammar_prompt = f"Check grammar, spelling, and phrasing: '{user_input}'. Provide corrections and explanations."
    grammar_response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{"role": "system", "content": grammar_prompt}],
        max_tokens=120
    )
    grammar_reply = grammar_response.choices[0].message.content.strip()
    st.info(f"📝 **Sir Felix's Correction:** {grammar_reply}")

# --- Speaking (Speech Recognition) ---
st.markdown("---")
st.subheader("🎙️ Speak to Sir Felix")

def audio_frame_callback(frame):
    audio = frame.to_ndarray(format="flt32", layout="mono")
    return av.AudioFrame.from_ndarray(audio, format="flt32", layout="mono")

webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDRECV,
    audio_frame_callback=audio_frame_callback,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if webrtc_ctx.audio_receiver:
    audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=2)
    audio_bytes = b''.join([frame.to_ndarray(format="pcm_s16le").tobytes() for frame in audio_frames])

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

        if st.button("🗣️ Transcribe and Correct"):
            transcript = recognize_speech(audio_bytes, language_codes.get(language, "en-US"))
            st.success(f"🎧 Transcription: {transcript}")

            grammar_prompt = f"Check grammar, spelling, phrasing: '{transcript}'. Provide corrections and explanations."
            grammar_response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "system", "content": grammar_prompt}],
                max_tokens=120
            )
            grammar_reply = grammar_response.choices[0].message.content.strip()
            st.info(f"📝 **Correction:** {grammar_reply}")

st.caption("🔖 Ensure microphone permissions are enabled. Best on Chrome or Firefox.")
