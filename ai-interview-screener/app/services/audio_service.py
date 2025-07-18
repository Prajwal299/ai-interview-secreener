# import speech_recognition as sr
# import pyttsx3
# import requests
# import os
# from flask import current_app
# import uuid

# class AudioService:
#     def __init__(self):
#         self.recognizer = sr.Recognizer()
#         self.tts_engine = pyttsx3.init()
#         self.upload_folder = current_app.config['UPLOAD_FOLDER']
    
#     def speech_to_text(self, audio_file_path):
#         """Convert speech to text using Google Speech Recognition"""
#         try:
#             with sr.AudioFile(audio_file_path) as source:
#                 audio = self.recognizer.record(source)
            
#             # Use Google's free speech recognition service
#             text = self.recognizer.recognize_google(audio)
#             return text
            
#         except sr.UnknownValueError:
#             return "Could not understand audio"
#         except sr.RequestError as e:
#             return f"Could not request results; {e}"
    
#     def text_to_speech(self, text, output_file=None):
#         """Convert text to speech"""
#         if output_file is None:
#             output_file = os.path.join(self.upload_folder, f"tts_{uuid.uuid4().hex}.wav")
        
#         self.tts_engine.save_to_file(text, output_file)
#         self.tts_engine.runAndWait()
        
#         return output_file
    
#     def download_recording(self, recording_url, call_sid):
#         """Download Twilio recording"""
#         try:
#             # Add Twilio auth to the URL
#             auth = (current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
#             response = requests.get(recording_url, auth=auth)
            
#             if response.status_code == 200:
#                 filename = f"recording_{call_sid}_{uuid.uuid4().hex}.wav"
#                 file_path = os.path.join(self.upload_folder, filename)
                
#                 with open(file_path, 'wb') as f:
#                     f.write(response.content)
                
#                 return file_path
#             else:
#                 raise Exception(f"Failed to download recording: {response.status_code}")
                
#         except Exception as e:
#             raise Exception(f"Error downloading recording: {str(e)}")


import logging
import requests
import speech_recognition as sr
import os
from flask import current_app
import uuid

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder, exist_ok=True)
    
    def speech_to_text(self, audio_file_path):
        """Convert speech to text using Google Speech Recognition or pocketsphinx fallback"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Try Google Speech-to-Text
            try:
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Transcript from Google: {text}")
                return text
            except sr.RequestError as e:
                logger.warning(f"Google Speech API failed: {e}. Falling back to pocketsphinx.")
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