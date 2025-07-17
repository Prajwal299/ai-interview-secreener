import os
import logging
from flask import current_app
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say

# Get a logger for this module
logger = logging.getLogger(__name__)

# ... (imports and __init__ function remain the same) ...

class TwilioService:
    def __init__(self):
        # ... same as before ...
        self.account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        self.auth_token = current_app.config['TWILIO_AUTH_TOKEN']
        self.from_number = current_app.config['TWILIO_PHONE_NUMBER']
        self.base_url = current_app.config['BASE_URL'] # Should be http://13.201.187.228:5000
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.error("Twilio credentials are not fully configured.")
            raise ValueError("Twilio credentials are not fully configured.")
            
        self.client = Client(self.account_sid, self.auth_token)
        logger.info(f"TwilioService initialized. From: {self.from_number}, Base URL: {self.base_url}")


    def start_campaign_calls(self, campaign):
        """Iterates through candidates in a campaign and initiates calls."""
        logger.info(f"Starting campaign calls for campaign_id: {campaign.id}")
        
        candidates_to_call = campaign.candidates
        
        if not candidates_to_call:
            logger.warning(f"No candidates found for campaign_id: {campaign.id}. No calls will be made.")
            return []

        logger.info(f"Found {len(candidates_to_call)} candidates to call for campaign {campaign.id}.")

        call_results = []
        for candidate in candidates_to_call:
            try:
                # The webhook for when the call is ANSWERED
                call_handler_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}"
                
                # The webhook for when the call STATUS CHANGES (e.g., ringing, completed, failed)
                status_callback_url = f"{self.base_url}/api/voice/status"

                logger.debug(f"Attempting to call {candidate.phone_number} | Call Handler: {call_handler_url} | Status Callback: {status_callback_url}")

                call = self.client.calls.create(
                    to=candidate.phone_number,
                    from_=self.from_number,
                    url=call_handler_url, # TwiML for when the call is answered
                    method='POST',
                    
                    # === THIS IS THE PART YOU NEED TO ADD ===
                    status_callback=status_callback_url,
                    status_callback_method='POST',
                    # This specifies which events you want to be notified about
                    status_callback_event=['initiated', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no-answer'] 
                    # =========================================
                )
                
                logger.info(f"Successfully initiated call to {candidate.phone_number}. Call SID: {call.sid}")
                
                candidate.status = 'dialing' # Or 'initiated'
                candidate.call_sid = call.sid
                
                call_results.append({'candidate_id': candidate.id, 'call_sid': call.sid, 'status': 'initiated'})
                
            except Exception as e:
                logger.error(f"Failed to create call for candidate {candidate.id} ({candidate.phone_number}): {e}")
                candidate.status = 'failed'
                call_results.append({'candidate_id': candidate.id, 'error': str(e), 'status': 'failed'})
        
        from app import db
        db.session.commit()
        
        logger.info(f"Campaign {campaign.id} call results: {call_results}")
        return call_results

    def handle_call(self, candidate_id):
        """Generates TwiML for an answered call."""
        from app.models import Candidate, InterviewQuestion
        
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            logger.error(f"Call handler received request for non-existent candidate_id: {candidate_id}")
            return self.generate_error_response("We could not find your details.")

        logger.info(f"Handling incoming answered call for candidate {candidate.name} (ID: {candidate.id})")
        
        response = VoiceResponse()
        response.say(f"Hello {candidate.name}. This is an automated screening call for the {candidate.campaign.name} position.")
        response.pause(length=1)

        # Here you would loop through questions, record responses, etc.
        # This is a simplified example.
        questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()

        if not questions:
            response.say("There are no questions for this interview. Thank you for your time. Goodbye.")
            logger.warning(f"No questions found for campaign {candidate.campaign_id}.")
        else:
            response.say(questions[0].text)
            # Example for recording
            # response.record(action=f'/api/voice/recording_handler?question_id={questions[0].id}', maxLength=60)
            response.say("This was a demonstration. Thank you. Goodbye.")
        
        response.hangup()
        
        return response

    def generate_error_response(self, message="An error occurred. Please try again later. Goodbye."):
        """Generates a generic TwiML error response."""
        response = VoiceResponse()
        response.say(message)
        response.hangup()
        return response