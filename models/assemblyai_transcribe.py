import assemblyai as aai

# Set your AssemblyAI API key
aai.settings.api_key = "a01a82cda8144186abf143020a1ab062"  # Replace with your actual key


def transcribe_assemblyai(file_path, language="fr"):
    """
    Transcribe audio using AssemblyAI.

    Args:
        file_path (str): Path to the audio file.
        language (str): Language code for transcription.

    Returns:
        str: Transcription result or an error message.
    """
    try:
        # Initialize the AssemblyAI transcriber
        transcriber = aai.Transcriber()

        # Create transcription configuration
        config = aai.TranscriptionConfig(language_code=language)

        # Perform transcription (no need for await here)
        transcript = transcriber.transcribe(file_path, config=config)
        return transcript.text
    except Exception as e:
        return f"Error with AssemblyAI: {str(e)}"
