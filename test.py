import requests
import json

SPEECHMATICS_API_KEY = "ZYd6s7o9pBJV58Scj7b8Oi4TmHrixLud" # "zie22PmK7erzX8ttPspOZk5SZDgLYFrZ"
SPEECHMATICS_API_URL = "https://asr.api.speechmatics.com/v2/jobs/"

def upload_audio_to_speechmatics(file_path):
    """
    Upload an audio file to Speechmatics and initiate transcription.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        str: Job ID if successful, otherwise an error message.
    """
    try:
        # Open the audio file
        with open(file_path, "rb") as audio_file:
            # Headers for authorization
            headers = {"Authorization": f"Bearer {SPEECHMATICS_API_KEY}"}
            
            # Corrected payload: Only include supported properties
            payload = {
                "type": "transcription",
                "language": "fr"  # Set language to French
            }
            
            # Files for multipart/form-data
            files = {
                "data_file": audio_file,
                "config": (None, json.dumps(payload), "application/json")
            }

            # Make the POST request
            response = requests.post(SPEECHMATICS_API_URL, headers=headers, files=files)
            response.raise_for_status()

            # Extract Job ID from the response
            job_id = response.json().get("id")
            return job_id
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e.response.text}")
        return f"Error uploading to Speechmatics: {e.response.text}"


print(upload_audio_to_speechmatics("./audio_files/1.wav"))
