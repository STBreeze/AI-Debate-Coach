import os
import speech_recognition as sr
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai  # Google Gemini API
import re

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")  # Use Gemini-Pro for text-based tasks

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Welcome to the AI Debate Coach Backend 🎤</h1>"

@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    """Converts speech to text using Google Speech Recognition."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    audio_file = request.files["file"]
    file_path = "input.wav"
    audio_file.save(file_path)

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return jsonify({"transcription": text})
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio"}), 400
    except sr.RequestError:
        return jsonify({"error": "Speech Recognition API unavailable"}), 500

@app.route("/evaluate-argument", methods=["POST"])
def evaluate_argument():
    """Uses AI to analyze rationality, provide feedback, and improve the argument."""
    data = request.get_json()
    if not data or "text" not in data or "topic" not in data:
        return jsonify({"error": "No text or topic provided"}), 400

    topic = data["topic"]
    argument = data["text"]

    # AI prompt for evaluation
    prompt = f"""
    You are an AI debate coach. The topic of the debate is: "{topic}". The user's argument is: {argument}

    Please evaluate the following argument and provide a single, consolidated response that includes:
    - A **Rationality Score** between 0 (highly emotional) and 1 (highly rational), with a brief explanation of the score.
    - **Feedback** on the argument covering:
        - Logical Structure
        - Clarity & Coherence
        - Supporting Evidence
        - Potential Counterarguments (include at least one concrete counterpoint)
    - An **Improved Argument** that incorporates the feedback and strengthens the original argument.

    Please format your response like this:
    ---
    **Rationality Score:** X.X  
    **Reasoning for Score:** [Your explanation]

    **Feedback:**  
    [Your consolidated feedback covering all criteria]

    **Improved Argument:**  
    [The improved version of the argument]
    """

    try:
        response = model.generate_content(prompt)

        # Handle blocked responses gracefully
        if not response.parts or not response.text:
            return jsonify({
                "error": "⚠️ AI could not generate a response due to content restrictions. Please rephrase your argument."
            }), 400

        ai_output = response.text.strip()

        # Extract rationality score
        score_line = next((line for line in ai_output.split("\n") if "Rationality Score:" in line), None)
        rationality_score = float(re.search(r"[-+]?\d*\.\d+|\d+", score_line).group()) if score_line else 0.5

        # Extract reason for score
        reason_start = ai_output.find("**Reasoning for Score:**")
        reason_for_score = ai_output[reason_start:].strip() if reason_start != -1 else "No reasoning provided."

        # Extract feedback
        feedback_start = ai_output.find("**Feedback:**")
        feedback = ai_output[feedback_start:].strip() if feedback_start != -1 else "No feedback provided."

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "rationality_score": rationality_score,
        "reason_for_score": reason_for_score,
        "feedback": feedback
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
