from flask import Flask
from flask import render_template
from flask import request
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

    if file.filename != "":

        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        file.save(save_path)

        return f"Saved: {file.filename}"

    return "No file selected"

if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True)
