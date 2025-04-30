from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit
from models.assemblyai_transcribe import transcribe_assemblyai
from models.deepgram_transcribe import transcribe_deepgram
from models.aws_transcribe import transcribe_aws
from models.azure_transcribe import transcribe_azure
from models.speechmatics_transcribe import transcribe_with_speechmatics
import os

# Flask and SocketIO Setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Audio Files Directory
AUDIO_FOLDER = "./audio_files"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

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

    if not uploaded_files:
        return jsonify({"error": "No valid files uploaded"}), 400

    return jsonify({"filenames": uploaded_files})

@socketio.on("play_audio")
def handle_audio_playback(filename):
    file_path = os.path.join(AUDIO_FOLDER, filename)
    try:
        emit("transcription_result", {"file_name": filename})

        # AssemblyAI Transcription
        try:
            assemblyai_transcription = transcribe_assemblyai(file_path, language="fr")
            emit("model_result", {"file_name": filename, "model": "AssemblyAI", "result": assemblyai_transcription})
        except Exception as e:
            emit("model_result", {"file_name": filename, "model": "AssemblyAI", "result": f"Error: {str(e)}"})

        # Deepgram Transcription
        try:
            deepgram_transcription = transcribe_deepgram(file_path)
            emit("model_result", {"file_name": filename, "model": "Deepgram", "result": deepgram_transcription})
        except Exception as e:
            emit("model_result", {"file_name": filename, "model": "Deepgram", "result": f"Error: {str(e)}"})

        # AWS Transcription
        try:
            aws_transcription = transcribe_aws(file_path)
            emit("model_result", {"file_name": filename, "model": "AWS", "result": aws_transcription})
        except Exception as e:
            emit("model_result", {"file_name": filename, "model": "AWS", "result": f"Error: {str(e)}"})

        # Azure Transcription (ensure this block exists)
        try:
            azure_transcription = transcribe_azure(file_path)
            emit("model_result", {"file_name": filename, "model": "Azure", "result": azure_transcription})
        except Exception as e:
            emit("model_result", {"file_name": filename, "model": "Azure", "result": f"Error: {str(e)}"})

        try:
            speechmatics_transcription = transcribe_with_speechmatics(file_path)
            emit("model_result", {"file_name": filename, "model": "Speechmatics", "result": speechmatics_transcription})
        except Exception as e:
            emit("model_result", {"file_name": filename, "model": "Speechmatics", "result": f"Error: {str(e)}"})

    except Exception as e:
        emit("transcription_result", {"error": f"Error: {str(e)}"})


if __name__ == "__main__":
    socketio.run(app, debug=True)
