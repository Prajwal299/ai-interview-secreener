import logging
from flask_restful import Resource
from flask import request
from app.services.twilio_service import TwilioService
from app.services.audio_service import AudioService
from app.services.ai_service import AIService
from app.models import Campaign, Candidate
from app import db
logger = logging.getLogger(__name__)

class CallHandlerResource(Resource):
    def post(self):
        # This is the webhook Twilio hits when a call is answered
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        
        # We passed the candidate_id in the URL, which is much more reliable
        candidate_id = request.args.get('candidate_id')

        logger.info(f"Received incoming call webhook for CallSid: {call_sid}, CandidateID: {candidate_id}")

        if not candidate_id:
            logger.error(f"Call handler webhook was called without a candidate_id. From: {from_number}")
            twiml_response = TwilioService().generate_error_response()
            return str(twiml_response), 200, {'Content-Type': 'text/xml'}
            
        try:
            twilio_service = TwilioService()
            twiml_response = twilio_service.handle_call(candidate_id)
            logger.info(f"Generated TwiML for call {call_sid}")
            return str(twiml_response), 200, {'Content-Type': 'text/xml'}
        except Exception as e:
            logger.error(f"Error handling call for candidate_id {candidate_id}: {e}", exc_info=True)
            twiml_response = TwilioService().generate_error_response()
            return str(twiml_response), 200, {'Content-Type': 'text/xml'}

# ... rest of the file (RecordingHandlerResource, CampaignResultsResource) ...
class RecordingHandlerResource(Resource):
    def post(self):
        # This endpoint handles Twilio recording callbacks
        recording_url = request.form.get('RecordingUrl')
        call_sid = request.form.get('CallSid')
        
        # Process the recording
        audio_service = AudioService()
        ai_service = AIService()
        
        # Download and process the recording
        try:
            # Download the recording
            audio_file_path = audio_service.download_recording(recording_url, call_sid)
            
            # Convert speech to text
            transcript = audio_service.speech_to_text(audio_file_path)
            
            # Get AI analysis
            ai_analysis = ai_service.analyze_response(transcript)
            
            # Save to database (you'll need to implement logic to associate with correct candidate/question)
            # This is a simplified version - in practice, you'd need to track the call flow
            
            return {'message': 'Recording processed successfully'}, 200
            
        except Exception as e:
            return {'message': f'Error processing recording: {str(e)}'}, 500

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
    
class CallStatusHandlerResource(Resource):
    def post(self):
        """
        Receives status updates from Twilio for outbound calls.
        This is not for TwiML, it's for tracking call progress.
        """
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus') # e.g., 'initiated', 'ringing', 'completed'
        
        logger.info(f"Received call status update for CallSid: {call_sid}. New status: {call_status}")

        # Find the candidate associated with this call and update their status in the DB
        candidate = Candidate.query.filter_by(call_sid=call_sid).first()
        if candidate:
            candidate.status = call_status
            db.session.commit()
            logger.info(f"Updated status for candidate {candidate.id} to '{call_status}'")
        else:
            logger.warning(f"Received status update for a CallSid ({call_sid}) not found in the database.")
            
        # Twilio expects a 200 OK response to acknowledge receipt of the callback
        return '', 200 