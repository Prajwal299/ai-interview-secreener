# app/api/interview_routes.py

import logging
from flask_restful import Resource
from flask import request
from twilio.twiml.voice_response import VoiceResponse
from app.services.twilio_service import TwilioService
from app.models import Candidate, Campaign
from app import db
from flask import Response

logger = logging.getLogger(__name__)

# This is the entry point when a call is first answered.
class CallHandlerResource(Resource):
    def post(self):
        call_sid = request.form.get('CallSid')
        candidate_id = request.args.get('candidate_id')
        logger.info(f"Initial call answered. SID: {call_sid}, CandidateID: {candidate_id}")

        if not candidate_id:
            logger.error(f"Call handler missing candidate_id.")
            response = VoiceResponse()
            response.say("An application error has occurred. Goodbye.", voice='alice')
            response.hangup()
            return Response(str(response), mimetype='application/xml', status=200)

        response = TwilioService().handle_call_flow(candidate_id, question_index=0)
        logger.info(f"TwiML Response: {str(response)}")
        return Response(str(response), mimetype='application/xml', status=200)

# This is the handler for AFTER the user presses a key.
class RecordingHandlerResource(Resource):
    def post(self):
        call_sid = request.form.get('CallSid')
        digits_pressed = request.form.get('Digits')
        candidate_id = request.args.get('candidate_id')
        question_id = request.args.get('question_id')
        next_question_index = request.args.get('next_question_index')

        logger.info(f"User pressed key '{digits_pressed}' for question {question_id}. Asking next question.")

        response = TwilioService().handle_call_flow(
            candidate_id=candidate_id, 
            question_index=int(next_question_index)
        )
        return Response(str(response), mimetype='application/xml', status=200)

# This handler receives status updates like 'ringing', 'completed', etc.
class CallStatusHandlerResource(Resource):
    def post(self):
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        logger.info(f"Status update for SID: {call_sid}. Status: '{call_status}'")
        candidate = Candidate.query.filter_by(call_sid=call_sid).first()
        if candidate:
            candidate.status = call_status
            db.session.commit()
            logger.info(f"Updated status for candidate {candidate.id} to '{call_status}'")
        else:
            logger.warning(f"Status update for a SID ({call_sid}) not found in the DB.")
        return Response("", status=200, mimetype='application/xml')

# This is your API endpoint to fetch results.
class CampaignResultsResource(Resource):
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