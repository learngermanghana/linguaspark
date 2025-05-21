import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta
import pandas as pd
import uuid
import random
import tempfile

# --- Audio recording (optional, handles missing package gracefully) ---
try:
    from streamlit_audiorec import st_audiorec
except ImportError:
    st_audiorec = None

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

# Hide Streamlit logo, hamburger, and footer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- (existing session, CSV, navigation code remains unchanged) ---
# ... [omitted for brevity] ...

# --- In Practice Mode, after the existing audio record section ---
st.markdown("### 🎤 Practice Your Pronunciation (optional)")
if st_audiorec is not None:
    audio_bytes = st_audiorec()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        st.success("Recording successful! (Sir Felix will review your pronunciation soon.)")
    else:
        st.caption("👆 Press the microphone to record. If it does not work, update your browser, or send your voice note to WhatsApp: 233205706589.")
else:
    st.warning("Audio recording is not supported in this environment or streamlit_audiorec is not installed.")
    st.caption("You can record a voice note and send it to WhatsApp: 233205706589.")

# --- New: Audio Upload Option ---
st.markdown("### 🎙️ Or Upload Your Own Audio")
uploaded_audio = st.file_uploader(
    "Upload an audio file for Sir Felix to review", 
    type=["wav", "mp3", "ogg", "m4a"]
)
if uploaded_audio:
    # Play back the uploaded audio
    st.audio(uploaded_audio, format=None)
    st.success("Audio file uploaded successfully! Sir Felix will review it soon.")
    
    # Optional: Transcribe with OpenAI Whisper
    try:
        # Save to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_audio.read())
            tmp.flush()
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp.name, "rb")
        )
        st.markdown("**Transcription:**")
        st.write(transcript.text)
    except Exception:
        st.info("Transcription failed or Whisper model not available.")

# --- (rest of Practice mode code continues unchanged) ---
# ...
