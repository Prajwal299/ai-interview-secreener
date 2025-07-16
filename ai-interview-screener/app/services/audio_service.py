import speech_recognition as sr
import pyttsx3
import requests
import os
from flask import current_app
import uuid

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.upload_folder = current_app.config['UPLOAD_FOLDER']
    
    def speech_to_text(self, audio_file_path):
        """Convert speech to text using Google Speech Recognition"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Use Google's free speech recognition service
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Could not request results; {e}"
    
    def text_to_speech(self, text, output_file=None):
        """Convert text to speech"""
        if output_file is None:
            output_file = os.path.join(self.upload_folder, f"tts_{uuid.uuid4().hex}.wav")
        
        self.tts_engine.save_to_file(text, output_file)
        self.tts_engine.runAndWait()
        
        return output_file
    
    def download_recording(self, recording_url, call_sid):
        """Download Twilio recording"""
        try:
            # Add Twilio auth to the URL
            auth = (current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
            response = requests.get(recording_url, auth=auth)
            
            if response.status_code == 200:
                filename = f"recording_{call_sid}_{uuid.uuid4().hex}.wav"
                file_path = os.path.join(self.upload_folder, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                return file_path
            else:
                raise Exception(f"Failed to download recording: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Error downloading recording: {str(e)}")