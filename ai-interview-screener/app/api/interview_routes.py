from flask_restful import Resource, reqparse
from flask import request
from app.models import Campaign, Candidate, InterviewQuestion, Interview
from app.services.twilio_service import TwilioService
from app.services.audio_service import AudioService
from app.services.ai_service import AIService
from app import db
import os

class CallHandlerResource(Resource):
    def post(self):
        # This endpoint handles incoming Twilio voice calls
        twilio_service = TwilioService()
        
        # Get parameters from Twilio
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        call_sid = request.form.get('CallSid')
        
        # Find candidate by phone number
        candidate = Candidate.query.filter_by(phone_number=from_number).first()
        
        if not candidate:
            return twilio_service.generate_error_response()
        
        # Update candidate status
        candidate.status = 'called'
        db.session.commit()
        
        # Generate TwiML response for the call
        twiml_response = twilio_service.handle_call(candidate)
        
        return str(twiml_response), 200, {'Content-Type': 'text/xml'}

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