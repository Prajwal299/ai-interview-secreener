# import logging
# import requests
# import speech_recognition as sr
# import os
# from flask import current_app
# import uuid
# from google.cloud import speech

# logger = logging.getLogger(__name__)

# class AudioService:
#     def __init__(self):
#         self.recognizer = sr.Recognizer()
#         self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
#         if not os.path.exists(self.upload_folder):
#             os.makedirs(self.upload_folder, exist_ok=True)

#     def speech_to_text(self, audio_file_path):
#         """Convert speech to text using Google Cloud Speech-to-Text or pocketsphinx fallback"""
#         logger.info(f"Processing audio file: {audio_file_path}")
#         try:
#             with sr.AudioFile(audio_file_path) as source:
#                 audio = self.recognizer.record(source)
            
#             # Try Google Cloud Speech-to-Text
#             try:
#                 client = speech.SpeechClient()
#                 with open(audio_file_path, 'rb') as audio_file:
#                     content = audio_file.read()
                
#                 audio = speech.RecognitionAudio(content=content)
#                 config = speech.RecognitionConfig(
#                     encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#                     sample_rate_hertz=16000,
#                     language_code="en-US",
#                     enable_automatic_punctuation=True
#                 )
                
#                 response = client.recognize(config=config, audio=audio)
#                 transcript = " ".join(result.alternatives[0].transcript for result in response.results)
#                 logger.info(f"Google Cloud transcript: {transcript}")
#                 return transcript
#             except Exception as e:
#                 logger.warning(f"Google Cloud Speech API failed: {e}. Falling back to pocketsphinx.")
#                 try:
#                     text = self.recognizer.recognize_sphinx(audio)
#                     logger.info(f"Pocketsphinx transcript: {text}")
#                     return text
#                 except sr.UnknownValueError:
#                     logger.error("Pocketsphinx could not understand audio")
#                     return ""
#                 except sr.RequestError as e:
#                     logger.error(f"Pocketsphinx request failed: {e}")
#                     return ""
#         except Exception as e:
#             logger.error(f"Error in speech_to_text: {str(e)}")
#             return ""

#     def download_recording(self, recording_url, call_sid):
#         """Download Twilio recording"""
#         try:
#             auth = (current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
#             response = requests.get(recording_url, auth=auth)
#             response.raise_for_status()
            
#             filename = f"recording_{call_sid}_{uuid.uuid4().hex}.wav"
#             file_path = os.path.join(self.upload_folder, filename)
            
#             with open(file_path, 'wb') as f:
#                 f.write(response.content)
            
#             logger.info(f"Downloaded recording to {file_path}")
#             return file_path
#         except Exception as e:
#             logger.error(f"Error downloading recording: {str(e)}")
#             raise


import logging
import requests
import os
import uuid
import wave
import json
from flask import current_app
from vosk import Model, KaldiRecognizer
import speech_recognition as sr

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
        self.vosk_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'vosk-model-small-en-us-0.15')
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder, exist_ok=True)
        if not os.path.exists(self.vosk_model_path):
            logger.error(f"Vosk model not found at {self.vosk_model_path}")
            raise FileNotFoundError(f"Vosk model not found at {self.vosk_model_path}")
        self.vosk_model = Model(self.vosk_model_path)

    def speech_to_text(self, audio_file_path):
        """Convert speech to text using Vosk"""
        logger.info(f"Processing audio file: {audio_file_path}")
        try:
            # Ensure audio is in the correct format (mono, 16kHz, WAV)
            with wave.open(audio_file_path, 'rb') as wf:
                if wf.getnchannels() != 1:
                    logger.error(f"Audio file {audio_file_path} is not mono")
                    return ""
                if wf.getframerate() not in [16000, 8000]:
                    logger.warning(f"Audio file {audio_file_path} sample rate {wf.getframerate()} not optimal for Vosk; expected 16000 or 8000")
                if wf.getsampwidth() != 2:
                    logger.error(f"Audio file {audio_file_path} sample width is not 16-bit")
                    return ""

                recognizer = KaldiRecognizer(self.vosk_model, wf.getframerate())
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    recognizer.AcceptWaveform(data)

                result = recognizer.FinalResult()
                transcript = json.loads(result).get('text', '')
                logger.info(f"Vosk transcript: {transcript}")
                return transcript if transcript else ""

        except Exception as e:
            logger.error(f"Error in speech_to_text with Vosk: {str(e)}")
            return ""

    def download_recording(self, recording_url, call_sid):
        """Download Twilio recording"""
        try:
            auth = (current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
            response = requests.get(recording_url, auth=auth)
            response.raise_for_status()
            
            filename = f"recording_{call_sid}_{uuid.uuid4().hex}.wav"
            file_path = os.path.join(self.upload_folder, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded recording to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error downloading recording: {str(e)}")
            raise