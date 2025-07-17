# import logging
# from flask import current_app
# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse, Say, Record, Hangup, Pause
# from sqlalchemy.orm import joinedload
# from app.models import Candidate, InterviewQuestion, Interview
# from app import db

# logger = logging.getLogger(__name__)

# class TwilioService:
#     def __init__(self):
#         self.account_sid = current_app.config['TWILIO_ACCOUNT_SID']
#         self.auth_token = current_app.config['TWILIO_AUTH_TOKEN']
#         self.from_number = current_app.config['TWILIO_PHONE_NUMBER']
#         self.base_url = current_app.config['BASE_URL']
        
#         if not all([self.account_sid, self.auth_token, self.from_number]):
#             logger.error("Twilio credentials are not fully configured.")
#             raise ValueError("Twilio credentials are not fully configured.")
            
#         self.client = Client(self.account_sid, self.auth_token)
#         logger.info(f"TwilioService initialized. From: {self.from_number}, Base URL: {self.base_url}")

#     def start_campaign_calls(self, campaign):
#         """
#         Initiates outbound calls to all candidates in a campaign.
#         """
#         logger.info(f"Starting campaign calls for campaign_id: {campaign.id}")
#         candidates_to_call = campaign.candidates
#         if not candidates_to_call:
#             logger.warning(f"No candidates found for campaign_id: {campaign.id}.")
#             return []

#         logger.info(f"Found {len(candidates_to_call)} candidates to call for campaign {campaign.id}.")
#         call_results = []
#         for candidate in candidates_to_call:
#             try:
#                 # ✅ FIX: This URL tells Twilio where to get instructions when the call is answered.
#                 handler_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}"
                
#                 # This URL is for status updates (ringing, completed, etc.)
#                 status_callback_url = f"{self.base_url}/api/voice/status"
                
#                 call = self.client.calls.create(
#                     url=handler_url,  # This parameter is crucial.
#                     to=candidate.phone_number,
#                     from_=self.from_number,
#                     method='POST',
#                     status_callback=status_callback_url,
#                     status_callback_method='POST',
#                     status_callback_event=['initiated', 'ringing', 'answered', 'completed'] # Simplified list to avoid warnings
#                 )
                
#                 logger.info(f"Successfully initiated call to {candidate.phone_number}. Call SID: {call.sid}")
#                 candidate.status = 'initiated'
#                 candidate.call_sid = call.sid
#                 call_results.append({'candidate_id': candidate.id, 'call_sid': call.sid, 'status': 'initiated'})
#             except Exception as e:
#                 logger.error(f"Failed to create call for candidate {candidate.id}: {e}", exc_info=True)
#                 candidate.status = 'failed'
#                 call_results.append({'candidate_id': candidate.id, 'error': str(e), 'status': 'failed'})
        
#         db.session.commit()
#         logger.info(f"Campaign {campaign.id} call results: {call_results}")
#         return call_results

#     def handle_call_flow(self, candidate_id, question_index=0):
#         """
#         Generates TwiML for the interview flow. This function is called recursively
#         (via webhooks) to ask one question at a time.
#         """
#         # ✅ FIX: Eagerly load the 'campaign' relationship to prevent potential
#         # database session issues in a multi-process Gunicorn environment.
#         candidate = Candidate.query.options(joinedload(Candidate.campaign)).get(candidate_id)
        
#         if not candidate:
#             logger.error(f"Call handler can't find candidate_id: {candidate_id}")
#             return self.generate_error_response()

#         response = VoiceResponse()
#         questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()

#         logger.info(f"Found {len(questions)} questions for campaign {candidate.campaign_id}.")

#         # This logic runs only for the very first question to give an introduction.
#         if question_index == 0:
#             # This line is now safe because candidate.campaign was pre-loaded.
#             intro_message = f"Hello {candidate.name}. This is an automated screening call for the {candidate.campaign.name} position. Please answer each question after the beep. Press the star key when you are finished."
#             response.say(intro_message, voice='alice') 
#             response.pause(length=1)

#         # Check if there are more questions to ask.
#         if question_index < len(questions):
#             current_question = questions[question_index]
#             logger.info(f"Asking question #{question_index + 1} to candidate {candidate.id}: '{current_question.text}'")
            
#             response.say(current_question.text, voice='alice')
            
#             # This is the URL Twilio will call AFTER the recording is done.
#             recording_handler_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
            
#             # Record the user's answer. The 'action' attribute is crucial.
#             response.record(
#                 action=recording_handler_url,
#                 method='POST',
#                 maxLength=120,
#                 finishOnKey='*',
#                 playBeep=True
#             )
#         else:
#             # All questions have been asked, so now we end the call.
#             logger.info(f"Interview completed for candidate {candidate.id}.")
#             response.say("Thank you for completing the interview. We will be in touch soon. Goodbye.", voice='alice')
#             response.hangup()

#         return response

#     def handle_recording(self, candidate_id, question_id, next_question_index, recording_url, call_sid):
#         """
#         Handles the webhook after a recording is finished. It saves the recording data
#         and then generates the TwiML for the *next* question.
#         """
#         logger.info(f"Received recording for C:{candidate_id} Q:{question_id}. URL: {recording_url}")
        
#         # Make sure your Interview model has a 'recording_url' field.
#         interview_record = Interview(
#             candidate_id=candidate_id,
#             question_id=question_id,
#             recording_url=recording_url
#         )
#         db.session.add(interview_record)
#         db.session.commit()

#         # Generate the TwiML to ask the next question in the sequence.
#         return self.handle_call_flow(candidate_id, question_index=int(next_question_index))

#     def generate_error_response(self, message="An application error has occurred. Goodbye."):
#         """
#         Generates a generic TwiML error response to hang up the call gracefully.
#         """
#         response = VoiceResponse()
#         response.say(message, voice='alice')
#         response.hangup()
#         return response


import logging
from flask import current_app
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say, Record, Hangup, Pause
from sqlalchemy.orm import joinedload
from app.models import Candidate, InterviewQuestion, Interview
from app import db

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        # ... this method is correct ...
        self.account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        self.auth_token = current_app.config['TWILIO_AUTH_TOKEN']
        self.from_number = current_app.config['TWILIO_PHONE_NUMBER']
        self.base_url = current_app.config['BASE_URL']
        self.client = Client(self.account_sid, self.auth_token)

    def start_campaign_calls(self, campaign):
        # ... this method is correct ...
        call_results = []
        for candidate in campaign.candidates:
            handler_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}"
            status_callback_url = f"{self.base_url}/api/voice/status"
            call = self.client.calls.create(
                url=handler_url,
                to=candidate.phone_number,
                from_=self.from_number,
                status_callback=status_callback_url,
                status_callback_method='POST'
            )
            candidate.status = 'initiated'
            candidate.call_sid = call.sid
            call_results.append({'candidate_id': candidate.id, 'call_sid': call.sid, 'status': 'initiated'})
        db.session.commit()
        return call_results

    def handle_call_flow(self, candidate_id, question_index=0):
        # ... this is the keypad version from before, which is correct ...
        candidate = Candidate.query.options(joinedload(Candidate.campaign)).get(candidate_id)
        if not candidate:
            response = VoiceResponse()
            response.say("An application error has occurred. Goodbye.")
            response.hangup()
            return response

        response = VoiceResponse()
        questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()

        if question_index == 0:
            response.say(f"Hello {candidate.name}. This is a test call. After each question, please press any key to continue.", voice='alice')
            response.pause(length=1)

        if question_index < len(questions):
            current_question = questions[question_index]
            response.say(current_question.text, voice='alice')
            response.say("Please press any key to continue.", voice='alice')
            
            gather_handler_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
            
            response.gather(input='dtmf', num_digits=1, action=gather_handler_url, method='POST')
        else:
            response.say("Thank you for completing the test. Goodbye.", voice='alice')
            response.hangup()

        return response
    

    def generate_error_response(self, message="An application error has occurred. Goodbye."):
        response = VoiceResponse()
        response.say(message, voice='alice')
        response.hangup()
        return response