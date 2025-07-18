

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




# import logging
# import requests
# import os
# import uuid
# import wave
# import json
# from flask import current_app
# from vosk import Model, KaldiRecognizer
# from pydub import AudioSegment

# logger = logging.getLogger(__name__)

# class AudioService:
#     def __init__(self):
#         self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
#         self.vosk_model_path = '/home/ubuntu/ai-interview-secreener/ai-interview-screener/vosk-model-small-en-us-0.15'
#         if not os.path.exists(self.upload_folder):
#             os.makedirs(self.upload_folder, exist_ok=True)
#         if not os.path.exists(self.vosk_model_path):
#             logger.error(f"Vosk model not found at {self.vosk_model_path}")
#             raise FileNotFoundError(f"Vosk model not found at {self.vosk_model_path}")
#         self.vosk_model = Model(self.vosk_model_path)

#     def convert_to_vosk_format(self, input_path, output_path):
#         """Convert audio to mono, 16-bit, 16kHz WAV format for Vosk"""
#         try:
#             audio = AudioSegment.from_wav(input_path)
#             audio = audio.set_channels(1)  # Convert to mono
#             audio = audio.set_frame_rate(16000)  # Set to 16kHz
#             audio = audio.set_sample_width(2)  # Set to 16-bit
#             audio.export(output_path, format="wav")
#             logger.info(f"Converted audio to {output_path} for Vosk")
#             return output_path
#         except Exception as e:
#             logger.error(f"Error converting audio: {str(e)}")
#             raise

#     def speech_to_text(self, audio_file_path):
#         """Convert speech to text using Vosk"""
#         logger.info(f"Processing audio file: {audio_file_path}")
#         try:
#             # Convert audio to Vosk-compatible format
#             converted_path = os.path.join(self.upload_folder, f"converted_{uuid.uuid4().hex}.wav")
#             self.convert_to_vosk_format(audio_file_path, converted_path)
#             # Ensure audio is in the correct format (mono, 16kHz, WAV)
#             with wave.open(converted_path, 'rb') as wf:
#                 if wf.getnchannels() != 1:
#                     logger.error(f"Audio file {converted_path} is not mono")
#                     return ""
#                 if wf.getframerate() not in [16000, 8000]:
#                     logger.warning(f"Audio file {converted_path} sample rate {wf.getframerate()} not optimal for Vosk; expected 16000 or 8000")
#                 if wf.getsampwidth() != 2:
#                     logger.error(f"Audio file {converted_path} sample width is not 16-bit")
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
#                 os.remove(converted_path)  # Clean up converted file
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
from flask import current_app
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
        self.vosk_model_path = '/home/ubuntu/ai-interview-secreener/ai-interview-screener/vosk-model-small-en-us-0.15'
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder, exist_ok=True)
        if not os.path.exists(self.vosk_model_path):
            logger.error(f"Vosk model not found at {self.vosk_model_path}")
            raise FileNotFoundError(f"Vosk model not found at {self.vosk_model_path}")
        self.vosk_model = Model(self.vosk_model_path)  # Load model once
        logger.info("Vosk model loaded successfully")

    def convert_to_vosk_format(self, input_path, output_path):
        """Convert audio to mono, 16-bit, 16kHz WAV format for Vosk"""
        try:
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_channels(1)  # Convert to mono
            audio = audio.set_frame_rate(16000)  # Set to 16kHz
            audio = audio.set_sample_width(2)  # Set to 16-bit
            audio.export(output_path, format="wav")
            logger.info(f"Converted audio to {output_path} for Vosk")
            return output_path
        except Exception as e:
            logger.error(f"Error converting audio {input_path}: {str(e)}")
            return None

    def speech_to_text(self, audio_file_path):
        """Convert speech to text using Vosk"""
        logger.info(f"Processing audio file: {audio_file_path}")
        try:
            # Convert audio to Vosk-compatible format
            converted_path = os.path.join(self.upload_folder, f"converted_{uuid.uuid4().hex}.wav")
            converted_file = self.convert_to_vosk_format(audio_file_path, converted_path)
            if not converted_file:
                logger.error(f"Failed to convert audio file {audio_file_path}")
                return ""

            # Verify audio format
            with wave.open(converted_file, 'rb') as wf:
                logger.info(f"Audio details: channels={wf.getnchannels()}, sample_rate={wf.getframerate()}, sample_width={wf.getsampwidth()}, frames={wf.getnframes()}")
                if wf.getnchannels() != 1:
                    logger.error(f"Audio file {converted_file} is not mono")
                    os.remove(converted_file)
                    return ""
                if wf.getframerate() not in [16000, 8000]:
                    logger.warning(f"Audio file {converted_file} sample rate {wf.getframerate()} not optimal for Vosk; expected 16000 or 8000")
                if wf.getsampwidth() != 2:
                    logger.error(f"Audio file {converted_file} sample width is not 16-bit")
                    os.remove(converted_file)
                    return ""

                recognizer = KaldiRecognizer(self.vosk_model, wf.getframerate())
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if not recognizer.AcceptWaveform(data):
                        logger.debug("Partial waveform processed")

                result = recognizer.FinalResult()
                transcript = json.loads(result).get('text', '')
                logger.info(f"Vosk transcript: {transcript}")
                os.remove(converted_file)  # Clean up
                return transcript if transcript else ""

        except Exception as e:
            logger.error(f"Error in speech_to_text for {audio_file_path}: {str(e)}")
            if 'converted_file' in locals() and os.path.exists(converted_file):
                os.remove(converted_file)
            return ""

    def download_recording(self, recording_url, call_sid):
        """Download Twilio recording"""
        try:
            auth = (current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
            response = requests.get(recording_url, auth=auth, timeout=10)
            response.raise_for_status()
            
            filename = f"recording_{call_sid}_{uuid.uuid4().hex}.wav"
            file_path = os.path.join(self.upload_folder, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded recording to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error downloading recording {recording_url}: {str(e)}")
            raise