from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from flask import current_app
import time

class TwilioService:
    def __init__(self):
        self.client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )
        self.phone_number = current_app.config['TWILIO_PHONE_NUMBER']
        self.base_url = current_app.config['BASE_URL']
    
    def start_campaign_calls(self, campaign):
        """Start calling all candidates in a campaign"""
        results = []
        
        for candidate in campaign.candidates:
            if candidate.status == 'pending':
                try:
                    call = self.client.calls.create(
                        to=candidate.phone_number,
                        from_=self.phone_number,
                        url=f"{self.base_url}/api/voice/call_handler",
                        method='POST'
                    )
                    
                    results.append({
                        'candidate_id': candidate.id,
                        'call_sid': call.sid,
                        'status': 'initiated'
                    })
                    
                    # Small delay between calls
                    time.sleep(1)
                    
                except Exception as e:
                    results.append({
                        'candidate_id': candidate.id,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    def handle_call(self, candidate):
        """Generate TwiML response for handling a call"""
        response = VoiceResponse()
        
        # Introduction
        intro_message = f"Hello {candidate.name}, thank you for your interest in our position. We will now conduct a brief phone interview. Please answer each question clearly after the tone."
        response.say(intro_message, voice='alice')
        
        # Get questions for this candidate's campaign
        questions = candidate.campaign.questions
        
        for i, question in enumerate(questions):
            # Ask the question
            response.say(f"Question {i+1}: {question.text}", voice='alice')
            
            # Record the response
            response.record(
                action=f"{self.base_url}/api/voice/recording_handler",
                method='POST',
                max_length=60,
                finish_on_key='#',
                play_beep=True
            )
        
        # End call
        response.say("Thank you for your time. We will review your responses and get back to you soon.", voice='alice')
        response.hangup()
        
        return response
    
    def generate_error_response(self):
        """Generate error response for unknown callers"""
        response = VoiceResponse()
        response.say("Sorry, we could not identify your number. Please contact us directly.", voice='alice')
        response.hangup()
        return response