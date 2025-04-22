# backend/app.py

from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
import google.generativeai as genai
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash-latest")


# Flask app setup
app = Flask(__name__)
CORS(app)

def extract_video_id(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ['www.youtube.com', 'youtube.com']:
        if query.path == '/watch':
            return parse_qs(query.query).get('v', [None])[0]
    return None

def get_video_title(video_id):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    return response["items"][0]["snippet"]["title"]

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'es'])
        return " ".join([entry['text'] for entry in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        return None

def summarize_with_gemini(text):
    chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
    full_summary = ""
    for chunk in chunks:
        response = model.generate_content(f"Summarize this transcript:\n{chunk}")
        full_summary += response.text.strip() + " "
    return full_summary.strip()


@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json()
    url = data.get("url", "")
    try:
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400

        title = get_video_title(video_id)
        transcript = get_transcript(video_id)
        if not transcript:
            return jsonify({"error": "Transcript not available in English, Hindi, or Spanish."})

        summary = summarize_with_gemini(transcript)

        return jsonify({
            "title": title,
            "summary": summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
