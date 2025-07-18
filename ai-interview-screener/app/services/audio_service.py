import logging
import requests
import speech_recognition as sr
import os
from flask import current_app
import uuid
from google.cloud import speech

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder, exist_ok=True)
    
    def speech_to_text(self, audio_file_path):
        """Convert speech to text using Google Cloud Speech-to-Text or pocketsphinx fallback"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Try Google Cloud Speech-to-Text
            try:
                client = speech.SpeechClient()
                with open(audio_file_path, 'rb') as audio_file:
                    content = audio_file.read()
                
                audio = speech.RecognitionAudio(content=content)
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                )
                
                response = client.recognize(config=config, audio=audio)
                transcript = " ".join(result.alternatives[0].transcript for result in response.results)
                logger.info(f"Transcript from Google Cloud: {transcript}")
                return transcript
            except Exception as e:
                logger.warning(f"Google Cloud Speech API failed: {e}. Falling back to pocketsphinx.")
                # Fallback to pocketsphinx
                text = self.recognizer.recognize_sphinx(audio)
                logger.info(f"Transcript from pocketsphinx: {text}")
                return text
                
        except sr.UnknownValueError:
            logger.error("Speech recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition request failed: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error in speech_to_text: {str(e)}")
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