import boto3
import time
import os
import requests
from datetime import datetime
import uuid

# AWS Configuration
AWS_REGION = "us-east-1"  # Replace with your AWS region
AWS_ACCESS_KEY = "AKIARHJJNDZ5M5J5UELV"  # Replace with your access key
AWS_SECRET_KEY = "4DGDTum2kQoP798vUYn1WvbbfZpIvXuYTj1BE3kF"  # Replace with your secret key
S3_BUCKET_NAME = "voice-owl-transcribe-audio-bucket"  # Replace with your bucket name


def transcribe_aws(file_path, language_code="fr-FR"):
    """
    Transcribe audio using AWS Transcribe with secure pre-signed S3 URL.

    Args:
        file_path (str): Path to the local audio file.
        language_code (str): Language code for transcription.

    Returns:
        str: Transcribed text or an error message.
    """
    try:
        # Initialize AWS clients
        s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
        transcribe_client = boto3.client(
            "transcribe",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )

        # Upload file to S3
        s3_key = os.path.basename(file_path)
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)

        # Generate pre-signed URL for the uploaded file
        media_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600  # 1 hour validity
        )

        # Generate unique job name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex
        job_name = f"transcription-job-{timestamp}-{unique_id}"

        # print("Starting Transcription Job with:")
        # print("Media URL:", media_url, flush=True)
        # print("Format: wav", flush=True)
        # print("Language:", language_code, flush=True)
        # print("Job Name:", job_name, flush=True)


        # Start transcription job
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_url},
            MediaFormat="wav",  # Adjust if needed
            LanguageCode=language_code,
        )

        # Wait for completion
        while True:
            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            if status["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
                break
            time.sleep(5)

        # Return result
        if status["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
            transcription_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            response = requests.get(transcription_url).json()
            return response["results"]["transcripts"][0]["transcript"]
        else:
            return "AWS Transcription failed."
    except Exception as e:
        return f"Error with AWS Transcribe: {str(e)}"


# import boto3
# import time
# import os
# import requests
# from datetime import datetime
# import uuid


# # AWS Configuration
# AWS_REGION = "us-east-1"  # Replace with your AWS region
# AWS_ACCESS_KEY = "AKIARHJJNDZ5M5J5UELV"  # Replace with your access key
# AWS_SECRET_KEY = "4DGDTum2kQoP798vUYn1WvbbfZpIvXuYTj1BE3kF"  # Replace with your secret key
# S3_BUCKET_NAME = "voice-owl-transcribe-audio-bucket"  # Replace with your updated bucket name

# # def upload_to_s3(file_path):
# #     """
# #     Upload a file to S3 and return the S3 URI.

# #     Args:
# #         file_path (str): Path to the local file.

# #     Returns:
# #         str: S3 URI of the uploaded file.
# #     """
# #     try:
# #         s3_client = boto3.client(
# #             "s3",
# #             region_name=AWS_REGION,
# #             aws_access_key_id=AWS_ACCESS_KEY,
# #             aws_secret_access_key=AWS_SECRET_KEY,
# #         )
# #         s3_key = os.path.basename(file_path)
# #         s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
# #         return f"s3://{S3_BUCKET_NAME}/{s3_key}"
# #     except Exception as e:
# #         raise RuntimeError(f"Error uploading to S3: {str(e)}")

# def upload_to_s3(file_path):
#     try:
#         s3_client = boto3.client(
#             "s3",
#             region_name=AWS_REGION,
#             aws_access_key_id=AWS_ACCESS_KEY,
#             aws_secret_access_key=AWS_SECRET_KEY,
#         )
#         s3_key = os.path.basename(file_path)

#         # Upload the file
#         s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)

#         # Generate pre-signed URL (valid for 1 hour)
#         presigned_url = s3_client.generate_presigned_url(
#             'get_object',
#             Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
#             ExpiresIn=3600
#         )

#         return presigned_url
#     except Exception as e:
#         raise RuntimeError(f"Error uploading to S3: {str(e)}")



# def transcribe_aws(file_path, language_code="fr-FR"):
#     """
#     Transcribe audio using AWS Transcribe.

#     Args:
#         file_path (str): Path to the local audio file.
#         language_code (str): Language code for transcription (default is French "fr-FR").

#     Returns:
#         str: Transcribed text or an error message.
#     """
#     try:
#         # Upload the file to S3
#         s3_uri = upload_to_s3(file_path)

#         # Start transcription job using presigned URL
#         transcribe_client.start_transcription_job(
#             TranscriptionJobName=job_name,
#             Media={"MediaFileUri": s3_uri},
#             MediaFormat="wav",
#             LanguageCode=language_code,
#         )
#         # Initialize AWS Transcribe client
#         transcribe_client = boto3.client(
#             "transcribe",
#             region_name=AWS_REGION,
#             aws_access_key_id=AWS_ACCESS_KEY,
#             aws_secret_access_key=AWS_SECRET_KEY,
#         )

#         # Generate a unique transcription job name using date, time, and a UUID
#         timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#         unique_id = uuid.uuid4().hex  # Generate a random UUID
#         job_name = f"transcription-job-{timestamp}-{unique_id}"  # Ensure absolute uniqueness


#         # Start transcription job
#         transcribe_client.start_transcription_job(
#             TranscriptionJobName=job_name,
#             Media={"MediaFileUri": s3_uri},
#             MediaFormat="wav",  # Adjust format if not .wav
#             LanguageCode=language_code,
#         )

#         # Wait for transcription to complete
#         while True:
#             status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
#             if status["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
#                 break
#             time.sleep(5)  # Wait for 5 seconds before checking again

#         # Check if the transcription was successful
#         if status["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
#             transcription_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
#             # Download the transcription result
#             response = requests.get(transcription_url).json()
#             return response["results"]["transcripts"][0]["transcript"]
#         else:
#             return "AWS Transcription failed."
#     except Exception as e:
#         return f"Error with AWS Transcribe: {str(e)}"
