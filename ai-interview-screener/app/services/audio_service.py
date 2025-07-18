

# import logging
# import requests
# import os
# import uuid
# import wave
# import json
# from flask import current_app
# from vosk import Model, KaldiRecognizer
# import speech_recognition as sr

# logger = logging.getLogger(__name__)

# class AudioService:
#     def __init__(self):
#         self.recognizer = sr.Recognizer()
#         self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
#         # Set Vosk model path to the project root
#         self.vosk_model_path = '/home/ubuntu/ai-interview-secreener/ai-interview-screener/vosk-model-small-en-us-0.15'
#         if not os.path.exists(self.upload_folder):
#             os.makedirs(self.upload_folder, exist_ok=True)
#         if not os.path.exists(self.vosk_model_path):
#             logger.error(f"Vosk model not found at {self.vosk_model_path}. Please ensure the model is unzipped correctly.")
#             raise FileNotFoundError(f"Vosk model not found at {self.vosk_model_path}")
#         try:
#             self.vosk_model = Model(self.vosk_model_path)
#             logger.info(f"Vosk model successfully loaded from {self.vosk_model_path}")
#         except Exception as e:
#             logger.error(f"Failed to load Vosk model: {str(e)}")
#             raise

#     def speech_to_text(self, audio_file_path):
#         """Convert speech to text using Vosk"""
#         logger.info(f"Processing audio file: {audio_file_path}")
#         try:
#             # Verify audio file exists
#             if not os.path.exists(audio_file_path):
#                 logger.error(f"Audio file not found: {audio_file_path}")
#                 return ""

#             # Ensure audio is in the correct format (mono, 16kHz or 8kHz, 16-bit)
#             with wave.open(audio_file_path, 'rb') as wf:
#                 if wf.getnchannels() != 1:
#                     logger.error(f"Audio file {audio_file_path} is not mono (channels: {wf.getnchannels()})")
#                     return ""
#                 if wf.getframerate() not in [8000, 16000]:
#                     logger.warning(f"Audio file {audio_file_path} sample rate {wf.getframerate()} not optimal for Vosk; expected 8000 or 16000")
#                     return ""
#                 if wf.getsampwidth() != 2:
#                     logger.error(f"Audio file {audio_file_path} sample width is not 16-bit (sampwidth: {wf.getsampwidth()})")
#                     return ""

#                 recognizer = KaldiRecognizer(self.vosk_model, wf.getframerate())
#                 while True:
#                     data = wf.readframes(4000)
#                     if len(data) == 0:
#                         break
#                     recognizer.AcceptWaveform(data)

#                 result = recognizer.FinalResult()
#                 transcript = json.loads(result).get('text', '')
#                 logger.info(f"Vosk transcript: {transcript}")
#                 return transcript if transcript else ""

#         except Exception as e:
#             logger.error(f"Error in speech_to_text with Vosk: {str(e)}")
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
import soundfile as sf
import tempfile
from flask import current_app
from vosk import Model, KaldiRecognizer
import speech_recognition as sr

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
        self.vosk_model_path = '/home/ubuntu/ai-interview-secreener/ai-interview-screener/vosk-model-small-en-us-0.15'
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder, exist_ok=True)
        if not os.path.exists(self.vosk_model_path):
            logger.error(f"Vosk model not found at {self.vosk_model_path}. Please ensure the model is unzipped correctly.")
            raise FileNotFoundError(f"Vosk model not found at {self.vosk_model_path}")
        try:
            self.vosk_model = Model(self.vosk_model_path)
            logger.info(f"Vosk model successfully loaded from {self.vosk_model_path}")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {str(e)}")
            raise

    def speech_to_text(self, audio_file_path):
        """Convert speech to text using Vosk"""
        logger.info(f"Processing audio file: {audio_file_path}")
        try:
            # Verify audio file exists
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return ""

            # Check and convert audio format if necessary
            with wave.open(audio_file_path, 'rb') as wf:
                if wf.getnchannels() != 1:
                    logger.error(f"Audio file {audio_file_path} is not mono (channels: {wf.getnchannels()})")
                    return ""
                if wf.getsampwidth() != 2:
                    logger.error(f"Audio file {audio_file_path} sample width is not 16-bit (sampwidth: {wf.getsampwidth()})")
                    return ""
                sample_rate = wf.getframerate()
                if sample_rate != 16000:
                    logger.info(f"Converting audio {audio_file_path} from {sample_rate} Hz to 16000 Hz")
                    data, orig_rate = sf.read(audio_file_path)
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        sf.write(temp_file.name, data, 16000, subtype='PCM_16')
                        audio_file_path = temp_file.name

            # Process with Vosk
            with wave.open(audio_file_path, 'rb') as wf:
                if wf.getnchannels() != 1 or wf.getframerate() != 16000 or wf.getsampwidth() != 2:
                    logger.error(f"Converted audio {audio_file_path} still invalid: channels={wf.getnchannels()}, sample_rate={wf.getframerate()}, sampwidth={wf.getsampwidth()}")
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

                # Clean up temporary file if created
                if sample_rate != 16000:
                    try:
                        os.unlink(audio_file_path)
                        logger.info(f"Deleted temporary audio file: {audio_file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file {audio_file_path}: {str(e)}")

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