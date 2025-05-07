from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit
from models.assemblyai_transcribe import transcribe_assemblyai
from models.deepgram_transcribe import transcribe_deepgram
from models.aws_transcribe import transcribe_aws
from models.azure_transcribe import transcribe_azure
from models.speechmatics_transcribe import transcribe_with_speechmatics
from utils.scoring_logic import calculate_scores
import os
import csv
import requests

# Flask and SocketIO Setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Directories
AUDIO_FOLDER = "./audio_files"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

audio_references = {}  # Store references from the CSV


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/list_audio_files", methods=["GET"])
def list_audio_files():
    files = os.listdir(AUDIO_FOLDER)
    return jsonify({"files": files})


@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist("audio")
    if not files:
        return jsonify({"error": "No files selected"}), 400

    uploaded_files = []
    for file in files:
        if file.filename == "":
            continue
        file_path = os.path.join(AUDIO_FOLDER, file.filename)
        file.save(file_path)
        uploaded_files.append(file.filename)

    return jsonify({"filenames": uploaded_files})


@app.route("/read_csv", methods=["POST"])
def read_csv_and_download():
    global audio_references
    csv_file_path = os.path.join(os.path.dirname(__file__), "audio_url.csv")
    if not os.path.exists(csv_file_path):
        return jsonify({"error": "CSV file not found"}), 404

    downloaded_files = []
    audio_references = {}  # Reset the dictionary
    try:
        with open(csv_file_path, "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 3:
                    continue

                url = row[0].strip()
                first_name = row[1].strip()
                last_name = row[2].strip()
                reference_name = f"{first_name} {last_name}"

                if not url:
                    continue

                try:
                    response = requests.get(url, stream=True)
                    if response.status_code == 200:
                        filename = os.path.basename(url)
                        file_path = os.path.join(AUDIO_FOLDER, filename)
                        with open(file_path, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        downloaded_files.append(filename)
                        audio_references[filename] = reference_name
                except Exception as e:
                    print(f"Error downloading {url}: {e}")

        return jsonify({
            "downloaded_files": downloaded_files,
            "audio_references": audio_references
        })
    except Exception as e:
        return jsonify({"error": f"Error processing CSV file: {str(e)}"}), 500


@socketio.on("play_audio")
def handle_audio_playback(filename):
    global audio_references
    file_path = os.path.join(AUDIO_FOLDER, filename)
    print(f"Resolved file path: {file_path}")
    # ✅ Add .wav if missing
    if not file_path.endswith(".wav"):
        new_path = file_path + ".wav"
        os.rename(file_path, new_path)
        file_path = new_path

    # print(f"Resolved file path: {file_path}", flush=True)

    try:
        reference_text = audio_references.get(filename, "Default Reference Text")
        emit("transcription_result", {"file_name": filename})

        models = [
            {"name": "AssemblyAI", "function": transcribe_assemblyai},
            {"name": "Deepgram", "function": transcribe_deepgram},
            {"name": "AWS", "function": transcribe_aws},
            {"name": "Azure", "function": transcribe_azure},
            {"name": "Speechmatics", "function": transcribe_with_speechmatics}
        ]

        for model in models:
            try:
                transcription = model["function"](file_path)
                scores = calculate_scores(transcription, reference_text)
                emit("model_result", {
                    "file_name": filename,
                    "model": model["name"],
                    "result": transcription,
                    "scores": scores
                })
            except Exception as e:
                emit("model_result", {
                    "file_name": filename,
                    "model": model["name"],
                    "result": f"Error: {str(e)}",
                    "scores": None
                })
    except Exception as e:
        emit("transcription_result", {"error": f"Error: {str(e)}"})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
