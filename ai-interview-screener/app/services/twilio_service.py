import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from twilio.base.exceptions import TwilioRestException
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )
        self.phone_number = current_app.config['TWILIO_PHONE_NUMBER']
        self.base_url = current_app.config['BASE_URL']
        logger.info("TwilioService initialized with Account SID: %s, Phone: %s, Base URL: %s",
                    current_app.config['TWILIO_ACCOUNT_SID'], self.phone_number, self.base_url)

    def start_campaign_calls(self, campaign):
        """Start calling all candidates in a campaign"""
        logger.info("Starting campaign calls for campaign_id: %s", campaign.id)
        results = []
        
        for candidate in campaign.candidates:
            if candidate.status == 'pending':
                try:
                    logger.debug("Initiating call to %s from %s", candidate.phone_number, self.phone_number)
                    call = self.client.calls.create(
                        to=candidate.phone_number,
                        from_=self.phone_number,
                        url=f"{self.base_url}/api/voice/call_handler",
                        method='POST'
                    )
                    logger.info("Call initiated: SID=%s, To=%s", call.sid, candidate.phone_number)
                    results.append({
                        'candidate_id': candidate.id,
                        'call_sid': call.sid,
                        'status': 'initiated'
                    })
                    # Small delay between calls
                    time.sleep(1)
                except TwilioRestException as e:
                    logger.error("Twilio API error for candidate %s: %s", candidate.phone_number, str(e))
                    results.append({
                        'candidate_id': candidate.id,
                        'status': 'failed',
                        'error': str(e)
                    })
                except Exception as e:
                    logger.error("Unexpected error for candidate %s: %s", candidate.phone_number, str(e))
                    results.append({
                        'candidate_id': candidate.id,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        logger.info("Campaign %s call results: %s", campaign.id, results)
        return results
    
    def handle_call(self, candidate):
        """Generate TwiML response for handling a call"""
        logger.info("Generating TwiML for candidate: %s", candidate.id)
        response = VoiceResponse()
        
        # Introduction
        intro_message = f"Hello {candidate.name}, thank you for your interest in our position. We will now conduct a brief phone interview. Please answer each question clearly after the tone."
        response.say(intro_message, voice='alice')
        logger.debug("Added intro message for candidate %s", candidate.name)
        
        # Get questions for this candidate's campaign
        questions = candidate.campaign.questions
        logger.debug("Found %d questions for campaign %s", len(questions), candidate.campaign.id)
        
        for i, question in enumerate(questions):
            # Ask the question
            response.say(f"Question {i+1}: {question.text}", voice='alice')
            logger.debug("Added question %d: %s", i+1, question.text)
            
            # Record the response
            response.record(
                action=f"{self.base_url}/api/voice/recording_handler",
                method='POST',
                max_length=60,
                finish_on_key='#',
                play_beep=True
            )
            logger.debug("Added recording action for question %d", i+1)
        
        # End call
        response.say("Thank you for your time. We will review your responses and get back to you soon.", voice='alice')
        response.hangup()
        logger.info("TwiML generated for candidate %s", candidate.id)
        
        return response
    
    def generate_error_response(self):
        """Generate error response for unknown callers"""
        logger.warning("Generating error response for unknown caller")
        response = VoiceResponse()
        response.say("Sorry, we could not identify your number. Please contact us directly.", voice='alice')
        response.hangup()
        return response