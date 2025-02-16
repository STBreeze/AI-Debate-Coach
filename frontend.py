import os
import streamlit as st
import requests
from audio_recorder_streamlit import audio_recorder
import io

st.title("🎤 AI Powered Debate Coach")

# Set backend URL using environment variable (or fallback to local)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5000")  # Uncomment for deployment

# Initialize session state variables
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "reason_for_score" not in st.session_state:
    st.session_state.reason_for_score = ""
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "rationality_score" not in st.session_state:
    st.session_state.rationality_score = None
if "improved_argument" not in st.session_state:
    st.session_state.improved_argument = ""
if "prev_audio_bytes" not in st.session_state:
    st.session_state.prev_audio_bytes = None  # Ensure it's always initialized

# **Text Input for Debate Topic**
st.subheader("🎯 Debate Topic")
st.session_state.topic = st.text_input(" ", st.session_state.topic, placeholder="Enter the topic of your argument here...")

st.subheader("📝 Your Argument")

# Get audio input from the recorder
audio_bytes = audio_recorder()

# Ensure prev_audio_bytes always updates
if audio_bytes:
    if st.session_state.get("prev_audio_bytes") is None or st.session_state.prev_audio_bytes != audio_bytes:
        st.session_state.prev_audio_bytes = audio_bytes  # Store the new recording
        st.session_state.audio_transcribed = False  # Reset processed flag

# Process the audio only if it's not empty and hasn't been transcribed yet
if audio_bytes and not st.session_state.get("audio_transcribed", False) and len(audio_bytes) > 1000:
    st.audio(audio_bytes, format="audio/wav")
    st.toast("Recording complete! Processing...", icon="✅")

    with st.spinner("🔍 Converting speech to text..."):
        files = {"file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
        response = requests.post(f"{BACKEND_URL}/speech-to-text", files=files)

    if response.status_code == 200:
        st.session_state.transcribed_text = response.json().get("transcription", "")
        st.session_state.audio_transcribed = True  # Mark as processed
    else:
        st.toast("Failed to process speech. Try again.", icon="❌")

# **Text Area for Editing Argument**
user_input = st.text_area(" ", st.session_state.transcribed_text, placeholder="Enter or edit your argument here...")
evaluate_button = st.button("✅ Evaluate Argument")

st.divider()

# **Submit Button for AI Evaluation**
if evaluate_button:
    final_argument = user_input if user_input.strip() else st.session_state.transcribed_text  # Use typed text if available

    # **Show loading spinner while AI processes**
    with st.spinner("🔍 Analyzing your argument..."):
        response = requests.post(f"{BACKEND_URL}/evaluate-argument", json={"topic": st.session_state.topic, "text": final_argument})

    if response.status_code == 200:
        result = response.json()
        st.session_state.rationality_score = result.get("rationality_score", None)
        st.session_state.reason_for_score = result.get("reason_for_score", "No reasoning provided.")
        st.session_state.feedback = result.get("feedback", "No feedback provided.")
        st.session_state.improved_argument = result.get("improved_argument", "No improved argument provided.")  # ✅ Ensure improved argument is saved

    elif response.status_code == 400:  # Handle Gemini's blocked response
        st.session_state.feedback = "⚠️ AI could not generate a response due to content restrictions. Please rephrase your argument."

    else:
        st.session_state.feedback = "❌ AI evaluation failed."

# **Display Rationality Score (Next to Subheading)**
if st.session_state.rationality_score is not None:
    st.subheader(f"📊 Rationality Score: {st.session_state.rationality_score:.2f}")
    st.progress(st.session_state.rationality_score)

    # Display reason for score below the meter
    if st.session_state.reason_for_score:
        st.write(f"**📝 Score Reasoning:** *{st.session_state.reason_for_score}*")

# **Display AI Feedback (Without Rationality Score)**
if st.session_state.feedback:
    st.subheader("🤖 AI Feedback:")
    st.write(st.session_state.feedback)

# ✅ **Fixed the Improved Argument Display**
if st.session_state.improved_argument:  # Ensure correct session state variable is used
    st.subheader("🗣️ Improved Argument:")
    st.write(st.session_state.improved_argument)
