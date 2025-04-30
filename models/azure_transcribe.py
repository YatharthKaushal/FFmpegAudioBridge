import azure.cognitiveservices.speech as speechsdk

# Azure Speech Service Configuration
AZURE_KEY = "9168d688958543128bb2250978299c3d"
AZURE_REGION = "eastus"

def transcribe_azure(file_path, language="fr-FR"):
    """
    Transcribe audio using Azure Speech-to-Text.

    Args:
        file_path (str): Path to the local audio file.
        language (str): Language code for transcription (default is French "fr-FR").

    Returns:
        str: Transcribed text or an error message.
    """
    try:
        # Create a Speech Config object
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
        speech_config.speech_recognition_language = language

        # Create an audio config from the file
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)

        # Create a Speech Recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Perform the transcription
        result = speech_recognizer.recognize_once()

        # Check the result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "No speech recognized in the audio file."
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return f"Transcription canceled: {cancellation_details.reason}. {cancellation_details.error_details}"
        else:
            return "Unknown transcription error."
    except Exception as e:
        return f"Error with Azure Transcription: {str(e)}"
