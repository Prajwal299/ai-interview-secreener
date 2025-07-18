# # app/api/interview_routes.py

# from datetime import datetime
# import logging
# from flask_restful import Resource
# from flask import request
# from twilio.twiml.voice_response import VoiceResponse
# from app.services.twilio_service import TwilioService
# from app.models import Candidate, Campaign, InterviewQuestion
# from app import db
# from flask import Response
# from app.models import Interview
# from app.services.audio_service import AudioService
# from app.services.ai_service import AIService


# logger = logging.getLogger(__name__)

# # This is the entry point when a call is first answered.
# class CallHandlerResource(Resource):
#     def post(self):
#         call_sid = request.form.get('CallSid')
#         candidate_id = request.args.get('candidate_id')
#         logger.info(f"Initial call answered. SID: {call_sid}, CandidateID: {candidate_id}")

#         if not candidate_id:
#             logger.error(f"Call handler missing candidate_id.")
#             response = VoiceResponse()
#             response.say("An application error has occurred. Goodbye.", voice='alice')
#             response.hangup()
#             return Response(str(response), mimetype='application/xml', status=200)

#         response = TwilioService().handle_call_flow(candidate_id, question_index=0)
#         logger.info(f"TwiML Response: {str(response)}")
#         return Response(str(response), mimetype='application/xml', status=200)

# # This is the handler for AFTER the user presses a key.
# class RecordingHandlerResource(Resource):
#     def post(self):
#         call_sid = request.form.get('CallSid')
#         digits_pressed = request.form.get('Digits')
#         recording_url = request.form.get('RecordingUrl')
#         candidate_id = request.args.get('candidate_id')
#         question_id = request.args.get('question_id')
#         next_question_index = request.args.get('next_question_index')

#         logger.info(f"Recording handler: SID={call_sid}, Digits={digits_pressed}, RecordingUrl={recording_url}, CandidateID={candidate_id}, QuestionID={question_id}")

#         if recording_url:
#             try:
#                 audio_service = AudioService()
#                 ai_service = AIService()
#                 file_path = audio_service.download_recording(recording_url, call_sid)
#                 transcript = audio_service.speech_to_text(file_path)
                
#                 question = InterviewQuestion.query.get(question_id)
#                 if not question:
#                     logger.error(f"Question ID {question_id} not found")
#                     return Response(str(VoiceResponse().say("An error occurred. Goodbye.", voice='alice').hangup()), 
#                                   mimetype='application/xml', status=200)

#                 scores = ai_service.analyze_response(transcript, question.text)
                
#                 interview = Interview(
#                     candidate_id=int(candidate_id),
#                     question_id=int(question_id),
#                     audio_recording_path=file_path,
#                     transcript=transcript,
#                     ai_score_communication=scores['communication_score'],
#                     ai_score_technical=scores['technical_score'],
#                     ai_recommendation=scores['recommendation'],
#                     created_at=datetime.utcnow()
#                 )
#                 db.session.add(interview)
#                 db.session.commit()
#                 logger.info(f"Saved interview record for candidate {candidate_id}, question {question_id}")
#             except Exception as e:
#                 logger.error(f"Error processing recording or scoring: {str(e)}")

#         if digits_pressed:
#             logger.info(f"User pressed key '{digits_pressed}' for question {question_id}. Asking next question.")
#             twiml_response = TwilioService().handle_call_flow(
#                 candidate_id=candidate_id, 
#                 question_index=int(next_question_index)
#             )
#             return Response(str(twiml_response), mimetype='application/xml', status=200)
#         else:
#             response = VoiceResponse()
#             response.say("No key pressed. Goodbye.", voice='alice')
#             response.hangup()
#             return Response(str(response), mimetype='application/xml', status=200)



# # This handler receives status updates like 'ringing', 'completed', etc.
# class CallStatusHandlerResource(Resource):
#     def post(self):
#         call_sid = request.form.get('CallSid')
#         call_status = request.form.get('CallStatus')
#         logger.info(f"Status update for SID: {call_sid}. Status: '{call_status}'")
#         candidate = Candidate.query.filter_by(call_sid=call_sid).first()
#         if candidate:
#             candidate.status = call_status
#             db.session.commit()
#             logger.info(f"Updated status for candidate {candidate.id} to '{call_status}'")
#         else:
#             logger.warning(f"Status update for a SID ({call_sid}) not found in the DB.")
#         return Response("", status=200, mimetype='application/xml')

# # This is your API endpoint to fetch results.
# class CampaignResultsResource(Resource):
#     def get(self, campaign_id):
#         campaign = Campaign.query.get_or_404(campaign_id)
#         results = []
#         for candidate in campaign.candidates:
#             interviews = Interview.query.filter_by(candidate_id=candidate.id).all()
#             total_communication = sum(i.ai_score_communication or 0 for i in interviews)
#             total_technical = sum(i.ai_score_technical or 0 for i in interviews)
#             count = len(interviews) or 1  # Avoid division by zero
#             avg_communication = total_communication // count
#             avg_technical = total_technical // count
#             # Shortlist if average scores meet a threshold (e.g., >= 70)
#             shortlisted = avg_communication >= 70 and avg_technical >= 70

#             candidate_result = {
#                 'candidate': candidate.to_dict(),
#                 'interviews': [interview.to_dict() for interview in interviews],
#                 'avg_communication_score': avg_communication,
#                 'avg_technical_score': avg_technical,
#                 'shortlisted': shortlisted
#             }
#             results.append(candidate_result)
        
#         return {'campaign': campaign.to_dict(), 'results': results}, 200
    

# class RecordingStatusHandlerResource(Resource):
#     def post(self):
#         call_sid = request.form.get('CallSid')
#         recording_sid = request.form.get('RecordingSid')
#         recording_url = request.form.get('RecordingUrl')
#         recording_status = request.form.get('RecordingStatus')
#         logger.info(f"Recording status update: SID={call_sid}, RecordingSID={recording_sid}, Status={recording_status}, URL={recording_url}")
#         return Response("", status=200, mimetype='application/xml')



from flask import Response, request
from flask_restful import Resource
from app.models import Interview, InterviewQuestion, Candidate, Campaign
from app.services.audio_service import AudioService
from app.services.ai_service import AIService
from app.services.twilio_service import TwilioService
from app import db
from datetime import datetime
import logging
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger(__name__)

class RecordingHandlerResource(Resource):
    def post(self):
        call_sid = request.form.get('CallSid')
        digits_pressed = request.form.get('Digits')
        recording_url = request.form.get('RecordingUrl')
        candidate_id = request.args.get('candidate_id')
        question_id = request.args.get('question_id')
        next_question_index = request.args.get('next_question_index')

        logger.info(f"Recording handler: SID={call_sid}, Digits={digits_pressed}, RecordingUrl={recording_url}, CandidateID={candidate_id}, QuestionID={question_id}, NextIndex={next_question_index}")

        if recording_url:
            try:
                audio_service = AudioService()
                ai_service = AIService()
                file_path = audio_service.download_recording(recording_url, call_sid)
                transcript = audio_service.speech_to_text(file_path)
                
                question = InterviewQuestion.query.get(question_id)
                if not question:
                    logger.error(f"Question ID {question_id} not found")
                    return Response(str(VoiceResponse().say("An error occurred. Goodbye.", voice='alice').hangup()), 
                                  mimetype='application/xml', status=200)

                if transcript:
                    scores = ai_service.analyze_response(transcript, question.text)
                    interview = Interview(
                        candidate_id=int(candidate_id),
                        question_id=int(question_id),
                        audio_recording_path=file_path,
                        transcript=transcript,
                        ai_score_communication=scores['communication_score'],
                        ai_score_technical=scores['technical_score'],
                        ai_recommendation=scores['recommendation'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(interview)
                    db.session.commit()
                    logger.info(f"Saved interview record for candidate {candidate_id}, question {question_id}")
                else:
                    logger.warning(f"No transcript generated for question {question_id}")
                
            except Exception as e:
                logger.error(f"Error processing recording or scoring: {str(e)}")

        if digits_pressed:
            logger.info(f"User pressed key '{digits_pressed}' for question {question_id}. Asking next question.")
            try:
                twiml_response = TwilioService().handle_call_flow(
                    candidate_id=candidate_id, 
                    question_index=int(next_question_index)
                )
                return Response(str(twiml_response), mimetype='application/xml', status=200)
            except Exception as e:
                logger.error(f"Error generating next question: {str(e)}")
                response = VoiceResponse()
                response.say("An error occurred. Goodbye.", voice='alice')
                response.hangup()
                return Response(str(response), mimetype='application/xml', status=200)
        else:
            logger.warning("No key pressed, ending call")
            response = VoiceResponse()
            response.say("No input received. Goodbye.", voice='alice')
            response.hangup()
            return Response(str(response), mimetype='application/xml', status=200)

class CampaignResultsResource(Resource):
    def get(self, campaign_id):
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                logger.error(f"Campaign ID {campaign_id} not found")
                return {"message": "Campaign not found"}, 404

            candidates = Candidate.query.filter_by(campaign_id=campaign_id).all()
            results = []

            for candidate in candidates:
                interviews = Interview.query.filter_by(candidate_id=candidate.id).all()
                interview_data = [interview.to_dict() for interview in interviews]

                # Calculate average scores
                if interview_data:
                    avg_communication = sum(i['ai_score_communication'] for i in interview_data if i['ai_score_communication'] is not None) / len(interview_data)
                    avg_technical = sum(i['ai_score_technical'] for i in interview_data if i['ai_score_technical'] is not None) / len(interview_data)
                    shortlisted = avg_communication >= 70 and avg_technical >= 70
                else:
                    avg_communication = 0
                    avg_technical = 0
                    shortlisted = False

                results.append({
                    "candidate": {
                        "id": candidate.id,
                        "name": candidate.name,
                        "phone_number": candidate.phone_number
                    },
                    "interviews": interview_data,
                    "avg_communication_score": round(avg_communication, 1),
                    "avg_technical_score": round(avg_technical, 1),
                    "shortlisted": shortlisted
                })

            return {
                "campaign": {
                    "id": campaign.id,
                    "name": campaign.name,
                    "job_description": campaign.job_description,
                    "status": campaign.status,
                    "created_at": campaign.created_at.isoformat()
                },
                "results": results
            }, 200

        except Exception as e:
            logger.error(f"Error retrieving campaign results: {str(e)}")
            return {"message": "Internal server error"}, 500