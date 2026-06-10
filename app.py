from flask import Flask, render_template, request
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload",methods=["POST"])
def upload_file():
    try:
        logger.info("Upload started")
        file = request.files.get("audio")
        if not file:
            logger.error("No audio file in request")
            return "Error: No audio file selected", 400
        
        context = request.form.get("context", "a presentation").strip()
        logger.info(f"Context: {context}")

        if file.filename == "":
            return "Error: No file selected", 400
        
        #Save upload file to server
        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        file.save(save_path)
        logger.info(f"File saved to {save_path}")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            return "Error: API key not configured", 500
        
        client = OpenAI(api_key=api_key)
        logger.info("Transcribing audio...")
        with open(save_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
            )
        text = transcript.text
        logger.info(f"Transcription complete: {len(text)} characters")

        #Analyze
        prompt = f"""You are a public speaking coach providing feedback on a speech.

The speaker is preparing for: {context}

Analyze this speech transcript and provide feedback in exactly this JSON format:
{{
  "filler_words": "count of um, uh, like, you know, basically, etc.",
  "pacing": "assessment of speaking speed (too fast/slow/good)",
  "strongest_moment": "quote from transcript + explanation",
  "top_improvement": "one specific actionable fix",
  "coach_note": "one encouraging sentence"
}}

Transcript: {text}"""

        logger.info("Getting AI feedback...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful public speaking coach. Always respond with valid, properly formatted content. Provide feedback that's specific to the speaker's context."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            timeout=30
        )
        feedback = response.choices[0].message.content
        logger.info("Feedback received successfully")

        return f"""
        <html>
        <head><title>Speech Coach - Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
            h2 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            .transcript {{ max-height: 200px; overflow-y: auto; }}
            .error {{ color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 5px; }}
        </style>
        </head>
        <body>
        <h1>Speech Coaching Results</h1>
        <h2>Your Transcript</h2>
        <div class="transcript"><pre>{text[:500]}...</pre></div>
        <h2>Coach Feedback</h2>
        <pre>{feedback}</pre>
        <p><a href="/">Upload another speech</a></p>
        </body>
        </html>
        """
    except Exception as e:
        logger.exception(f"Error during upload: {str(e)}")
        error_msg = str(e)
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
        <h2>Upload Failed</h2>
        <div class="error">
        <p><strong>Error:</strong> {error_msg}</p>
        <p><strong>Troubleshooting:</strong></p>
        <ul>
            <li>Check that your audio file is a valid MP3, WAV, or M4A format</li>
            <li>Verify the file size is under 25MB</li>
            <li>Ensure OPENAI_API_KEY is set correctly in .env</li>
            <li>Check your internet connection</li>
        </ul>
        <p><a href="/">Try again</a></p>
        </div>
        </body>
        </html>
        """, 500


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=False, use_reloader=False)
