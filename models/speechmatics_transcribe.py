import time
from speechmatics.models import ConnectionSettings, BatchTranscriptionConfig
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError
import traceback
import os

# Speechmatics API Key and Configuration
API_KEY = "ZYd6s7o9pBJV58Scj7b8Oi4TmHrixLud" # "PXx82LPEUVKzrv3N1PcQygZx9N0oS8IC"
LANGUAGE = "fr"  # Set language to French

# Define the Speechmatics API URL
API_URL = "https://asr.api.speechmatics.com/v2/jobs/"

def transcribe_with_speechmatics(file_path):
    """
    Transcribe audio using Speechmatics Batch API.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        str: Transcribed text or an error message.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."
    try:
        # Initialize connection settings with API key and URL
        connection_settings = ConnectionSettings(
            url=API_URL,
            auth_token=API_KEY
        )

        # Define transcription configuration
        transcription_config = BatchTranscriptionConfig(
            language=LANGUAGE,
            operating_point="standard",  # Use "standard" if "enhanced" is not supported
            output_format="txt"
        )

        # Use BatchClient to submit and retrieve transcription
        with BatchClient(connection_settings) as client:
            # Submit job
            job_id = client.submit_job(
                audio=file_path,
                transcription_config=transcription_config
            )
            print(f"Job {job_id} submitted successfully, waiting for transcript...")

            # Wait for completion and retrieve transcript
            transcript = client.wait_for_completion(job_id, transcription_format="txt")
            return transcript

    except HTTPStatusError as e:
        # Handle specific HTTP errors
        if e.response.status_code == 401:
            return "Error: Invalid API Key. Please check your API key."
        elif e.response.status_code == 400:
            return f"Error: {e.response.json().get('detail', 'Bad Request')}"
        elif e.response.status_code == 403:
            return "Error: Forbidden - Your API Key does not have the correct permissions."
        else:
            return f"Error: HTTP {e.response.status_code} - {e.response.text}"

    # except Exception as e:
    #     return f"Error with Speechmatics: {str(e)}"
    

    except Exception as e:
        return f"Error with Speechmatics: {str(e)}\nTraceback:\n{traceback.format_exc()}"
