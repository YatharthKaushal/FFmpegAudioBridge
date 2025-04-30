from deepgram import Deepgram
import asyncio

DEEPGRAM_API_KEY = "f557ec8051a22cde5b51b75aa19c4cc6e27a5bed"  # Replace with your API key

async def transcribe_with_deepgram(file_path):
    """
    Transcribe audio using Deepgram.

    Args:
        file_path (str): Path to the audio file to be transcribed.

    Returns:
        str: Transcribed text or an error message.
    """
    try:
        # Initialize the Deepgram client
        deepgram = Deepgram(DEEPGRAM_API_KEY)

        # Open the audio file
        with open(file_path, "rb") as audio:
            # Send the audio file to Deepgram for transcription
            source = {"buffer": audio, "mimetype": "audio/wav"}  # Change mimetype if not .wav
            response = await deepgram.transcription.prerecorded(source, {"language": "fr", "smart_format": True})  # French language
            return response["results"]["channels"][0]["alternatives"][0]["transcript"]
    except Exception as e:
        return f"Error with Deepgram: {str(e)}"

def transcribe_deepgram(file_path):
    """
    Wrapper function to run the async transcribe_with_deepgram function.
    """
    return asyncio.run(transcribe_with_deepgram(file_path))
