"""
app.py

Flask backend for the Music Chatbot.
Handles chat requests from the frontend and forwards them to the Gemini API,
using the persona/rules defined in chatbot_config.py.
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

from chatbot_config import SYSTEM_PROMPT

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.1-flash-lite"

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Please add it to your .env file."
    )

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the chat UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Receive a user message + conversation history, return the bot reply."""
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []  # list of {role, text}

    if not user_message:
        return jsonify({"error": "Empty message."}), 400

    try:
        contents = []
        for turn in history:
            role = "user" if turn.get("role") == "user" else "model"
            text = turn.get("text", "")
            if text:
                contents.append(
                    types.Content(role=role, parts=[types.Part(text=text)])
                )
        contents.append(
            types.Content(role="user", parts=[types.Part(text=user_message)])
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )

        reply_text = (response.text or "").strip()
        if not reply_text:
            reply_text = (
                "Sorry, I couldn't come up with a reply. Could you rephrase "
                "your music question?"
            )

        return jsonify({"reply": reply_text})

    except Exception as exc:  # noqa: BLE001
        app.logger.error("Gemini API error: %s", exc)
        return jsonify(
            {"error": "Something went wrong while talking to the AI. Please try again."}
        ), 500


if __name__ == "__main__":
    app.run(debug=True)
