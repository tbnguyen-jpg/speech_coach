from flask import Flask, render_template, request
from openai import OpenAI
from dotenv import load_dotenv
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload",methods=["POST"])
def upload_file():

    file = request.files["audio"]

    if file.filename == "":
        return "No file selected"
    
    save_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(save_path)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    with open(save_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
        )
    text = transcript.text

    return f"<h2>Trancript:</h2><p>{text}</p>"


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True)
