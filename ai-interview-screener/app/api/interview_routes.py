# app/api/interview_routes.py

import logging
from flask_restful import Resource
from flask import request
from app.models import Campaign, Candidate
from app.services.twilio_service import TwilioService
from app import db

# Note: The audio_service and ai_service are not used directly in these handlers
# anymore, as that logic is better placed in a background task after the call.
# from app.services.audio_service import AudioService
# from app.services.ai_service import AIService


logger = logging.getLogger(__name__)

class CallHandlerResource(Resource):
    """
    Handles the VERY FIRST webhook from Twilio when a call is answered.
    Its only job is to kick off the interview flow.
    """
    def post(self):
        # CORRECTED: The variable from Twilio is 'CallSid'
        call_sid = request.form.get('CallSid')
        candidate_id = request.args.get('candidate_id')
        logger.info(f"Initial call answered. SID: {call_sid}, CandidateID: {candidate_id}")

        if not candidate_id:
            logger.error(f"Call handler webhook called without a candidate_id.")
            return str(TwilioService().generate_error_response()), 200, {'Content-Type': 'text/xml'}
        
        # Start the interview flow from the beginning (question_index=0)
        # It will now call the advanced 'handle_call_flow' method
        twiml_response = TwilioService().handle_call_flow(candidate_id, question_index=0)
        return str(twiml_response), 200, {'Content-Type': 'text/xml'}

class RecordingHandlerResource(Resource):
    """
    Handles the webhook from Twilio AFTER each question's recording is complete.
    """
    def post(self):
        # CORRECTED: The variable from Twilio is 'CallSid'
        call_sid = request.form.get('CallSid')
        recording_url = request.form.get('RecordingUrl')
        candidate_id = request.args.get('candidate_id')
        question_id = request.args.get('question_id')
        next_question_index = request.args.get('next_question_index')

        logger.info(f"Recording received for SID: {call_sid}, C_ID: {candidate_id}, Q_ID: {question_id}")

        if not all([candidate_id, question_id, next_question_index, recording_url]):
            logger.error(f"Recording handler missing required parameters: {request.args}")
            return str(TwilioService().generate_error_response()), 200, {'Content-Type': 'text/xml'}

        # Process the recording (save it) and get TwiML for the next question.
        twiml_response = TwilioService().handle_recording(
            candidate_id, question_id, next_question_index, recording_url, call_sid
        )
        return str(twiml_response), 200, {'Content-Type': 'text/xml'}

class CallStatusHandlerResource(Resource):
    """
    Receives status updates from Twilio for outbound calls (e.g., ringing, completed).
    """
    def post(self):
        # CORRECTED: The variable from Twilio is 'CallSid'
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        logger.info(f"Status update for SID: {call_sid}. Status: '{call_status}'")

        # This requires the 'call_sid' column in your 'candidates' table.
        candidate = Candidate.query.filter_by(call_sid=call_sid).first()
        if candidate:
            candidate.status = call_status
            db.session.commit()
            logger.info(f"Updated status for candidate {candidate.id} to '{call_status}'")
        else:
            logger.warning(f"Status update for a SID ({call_sid}) not found in the DB.")
            
        # Acknowledge receipt to Twilio with a 200 OK.
        return '', 200

class CampaignResultsResource(Resource):
    """
    A standard API endpoint to fetch campaign results.
    """
    def get(self, campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        results = []
        for candidate in campaign.candidates:
            candidate_result = {
                'candidate': candidate.to_dict(),
                'interviews': [interview.to_dict() for interview in candidate.interviews]
            }
            results.append(candidate_result)
        
        return {'campaign': campaign.to_dict(), 'results': results}, 200