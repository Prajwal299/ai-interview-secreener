# # app/services/twilio_service.py

# import logging
# from flask import current_app
# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse, Say, Record, Hangup
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
#                 # This is the URL for the *first* TwiML instruction.
#                 handler_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}"
#                 status_callback_url = f"{self.base_url}/api/voice/status"
#                 logger.debug(f"Attempting to call {candidate.phone_number} | Handler: {handler_url} | Status: {status_callback_url}")
                
#                 call = self.client.calls.create(
#                     to=candidate.phone_number,
#                     from_=self.from_number,
#                     url=handler_url,
#                     method='POST',
#                     status_callback=status_callback_url,
#                     status_callback_method='POST',
#                     status_callback_event=['initiated', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no-answer']
#                 )
                
#                 logger.info(f"Successfully initiated call to {candidate.phone_number}. Call SID: {call.sid}")
#                 candidate.status = 'initiated'
#                 candidate.call_sid = call.sid # Save the SID to the candidate record
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
#         candidate = Candidate.query.get(candidate_id)
#         if not candidate:
#             logger.error(f"Call handler can't find candidate_id: {candidate_id}")
#             return self.generate_error_response()

#         response = VoiceResponse()
#         questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()

#         # On the very first call (index 0), give the introduction.
#         if question_index == 0:
#             response.say(f"Hello {candidate.name}. This is an automated screening call for the {candidate.campaign.name} position. Please answer each question after the beep, then press the star key.")
#             response.pause(length=1)

#         # Check if there are more questions to ask.
#         if question_index < len(questions):
#             current_question = questions[question_index]
#             logger.info(f"Asking question #{question_index + 1} to candidate {candidate.id}: '{current_question.text}'")
#             response.say(current_question.text)
            
#             # The 'action' URL is the webhook Twilio will call AFTER the recording is done.
#             # We pass all necessary info in the query string.
#             next_handler_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
            
#             response.record(
#                 action=next_handler_url,
#                 method='POST',
#                 maxLength=60, # 60 seconds max answer length
#                 finishOnKey='*' # User can press '*' to end the recording
#             )
            
#             # This part is a fallback. It's only executed if the <Record> verb fails or the user hangs up.
#             response.say("We did not receive a recording. Goodbye.")
#             response.hangup()
#         else:
#             # All questions have been asked, end the call.
#             logger.info(f"Interview completed for candidate {candidate.id}.")
#             response.say("Thank you for completing the interview. We will be in touch soon. Goodbye.")
#             response.hangup()

#         return response

#     def handle_recording(self, candidate_id, question_id, next_question_index, recording_url, call_sid):
#         """
#         Handles the webhook after a recording is finished. It saves the recording data
#         and then generates the TwiML for the *next* question.
#         """
#         logger.info(f"Received recording for C:{candidate_id} Q:{question_id}. URL: {recording_url}")
        
#         # Save a record of the interview answer to the database.
#         # The actual audio processing can be done later in a background job.
#         interview_record = Interview(
#             candidate_id=candidate_id,
#             question_id=question_id,
#             recording_url=recording_url
#         )
#         db.session.add(interview_record)
#         db.session.commit()

#         # Now, generate the TwiML to ask the next question in the sequence.
#         return self.handle_call_flow(candidate_id, question_index=int(next_question_index))

#     def generate_error_response(self, message="An error occurred. Goodbye."):
#         """
#         Generates a generic TwiML error response to hang up the call gracefully.
#         """
#         response = VoiceResponse()
#         response.say(message)
#         response.hangup()
#         return response



# app/services/twilio_service.py

import logging
from flask import current_app
from twilio.rest import Client
# Import Say, Record, Hangup, Pause (Pause was missing from original imports but used)
from twilio.twiml.voice_response import VoiceResponse, Say, Record, Hangup, Pause
from app.models import Candidate, InterviewQuestion, Interview
from app import db

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        self.auth_token = current_app.config['TWILIO_AUTH_TOKEN']
        self.from_number = current_app.config['TWILIO_PHONE_NUMBER']
        self.base_url = current_app.config['BASE_URL']
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.error("Twilio credentials are not fully configured.")
            raise ValueError("Twilio credentials are not fully configured.")
            
        self.client = Client(self.account_sid, self.auth_token)
        logger.info(f"TwilioService initialized. From: {self.from_number}, Base URL: {self.base_url}")

    def start_campaign_calls(self, campaign):
        """
        Initiates outbound calls to all candidates in a campaign.
        """
        logger.info(f"Starting campaign calls for campaign_id: {campaign.id}")
        candidates_to_call = campaign.candidates
        if not candidates_to_call:
            logger.warning(f"No candidates found for campaign_id: {campaign.id}.")
            return []

        logger.info(f"Found {len(candidates_to_call)} candidates to call for campaign {campaign.id}.")
        call_results = []
        for candidate in candidates_to_call:
            try:
                # This is the URL for the *first* TwiML instruction.
                handler_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}"
                status_callback_url = f"{self.base_url}/api/voice/status"
                logger.debug(f"Attempting to call {candidate.phone_number} | Handler: {handler_url} | Status: {status_callback_url}")
                
                call = self.client.calls.create(
                    to=candidate.phone_number,
                    from_=self.from_number,
                    url=handler_url,
                    method='POST',
                    status_callback=status_callback_url,
                    status_callback_method='POST',
                    status_callback_event=['initiated', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no-answer']
                )
                
                logger.info(f"Successfully initiated call to {candidate.phone_number}. Call SID: {call.sid}")
                candidate.status = 'initiated'
                candidate.call_sid = call.sid # Save the SID to the candidate record
                call_results.append({'candidate_id': candidate.id, 'call_sid': call.sid, 'status': 'initiated'})
            except Exception as e:
                logger.error(f"Failed to create call for candidate {candidate.id}: {e}", exc_info=True)
                candidate.status = 'failed'
                call_results.append({'candidate_id': candidate.id, 'error': str(e), 'status': 'failed'})
        
        db.session.commit()
        logger.info(f"Campaign {campaign.id} call results: {call_results}")
        return call_results

    def handle_call_flow(self, candidate_id, question_index=0):
        """
        Generates TwiML for the interview flow. This function is called recursively
        (via webhooks) to ask one question at a time.
        """
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            logger.error(f"Call handler can't find candidate_id: {candidate_id}")
            return self.generate_error_response()

        response = VoiceResponse()
        questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()

        # On the very first call (index 0), give the introduction.
        if question_index == 0:
            intro_message = f"Hello {candidate.name}. This is an automated screening call for the {candidate.campaign.name} position. Please answer each question after the beep, then press the star key."
            # Using 'voice=alice' often sounds better than the default
            response.say(intro_message, voice='alice') 
            response.pause(length=1)

        # Check if there are more questions to ask.
        if question_index < len(questions):
            current_question = questions[question_index]
            logger.info(f"Asking question #{question_index + 1} to candidate {candidate.id}: '{current_question.text}'")
            response.say(current_question.text, voice='alice')
            
            # The 'action' URL is the webhook Twilio will call AFTER the recording is done.
            # We pass all necessary info in the query string.
            next_handler_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
            
            response.record(
                action=next_handler_url,
                method='POST',
                maxLength=120, # Increased max answer length to 120s (2 mins)
                finishOnKey='*', # User can press '*' to end the recording
                playBeep=True    # Important: Play a beep so the user knows when to start talking
            )
            
            # --- FIX APPLIED HERE ---
            # The following lines were removed because they caused the call to hang up 
            # immediately after the <Record> verb started. The 'action' attribute 
            # handles the flow control after the recording is complete.

            # response.say("We did not receive a recording. Goodbye.")
            # response.hangup()
            
        else:
            # All questions have been asked, end the call.
            logger.info(f"Interview completed for candidate {candidate.id}.")
            response.say("Thank you for completing the interview. We will be in touch soon. Goodbye.", voice='alice')
            response.hangup()

        return response

    def handle_recording(self, candidate_id, question_id, next_question_index, recording_url, call_sid):
        """
        Handles the webhook after a recording is finished. It saves the recording data
        and then generates the TwiML for the *next* question.
        """
        logger.info(f"Received recording for C:{candidate_id} Q:{question_id}. URL: {recording_url}")
        
        # Save a record of the interview answer to the database.
        # The actual audio processing can be done later in a background job.
        interview_record = Interview(
            candidate_id=candidate_id,
            question_id=question_id,
            recording_url=recording_url
        )
        db.session.add(interview_record)
        db.session.commit()

        # Now, generate the TwiML to ask the next question in the sequence.
        return self.handle_call_flow(candidate_id, question_index=int(next_question_index))

    def generate_error_response(self, message="An error occurred. Goodbye."):
        """
        Generates a generic TwiML error response to hang up the call gracefully.
        """
        response = VoiceResponse()
        response.say(message, voice='alice')
        response.hangup()
        return response