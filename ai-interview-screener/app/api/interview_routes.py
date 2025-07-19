

from flask import Response, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Interview, InterviewQuestion, Candidate, Campaign
from app.services.audio_service import AudioService
from app.services.ai_service import AIService
from app.services.twilio_service import TwilioService
from app import db
from datetime import datetime
import logging
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger(__name__)

class CallHandlerResource(Resource):
    def post(self):
        candidate_id = request.args.get('candidate_id')
        logger.info(f"Call handler: candidate_id={candidate_id}")
        
        if not candidate_id:
            logger.error("No candidate_id provided")
            response = VoiceResponse()
            response.say("An error occurred. Goodbye.", voice='alice')
            response.hangup()
            return Response(str(response), mimetype='application/xml', status=200)
        
        twilio_service = TwilioService()
        twiml_response = twilio_service.handle_call_flow(candidate_id=candidate_id, question_index=0)
        return Response(twiml_response, mimetype='application/xml', status=200)

class RecordingHandlerResource(Resource):
    def post(self):
        call_sid = request.form.get('CallSid')
        digits_pressed = request.form.get('Digits')
        recording_url = request.form.get('RecordingUrl')
        candidate_id = request.args.get('candidate_id')
        question_id = request.args.get('question_id')
        next_question_index = request.args.get('next_question_index')

        logger.info(f"Recording handler: SID={call_sid}, Digits={digits_pressed}, RecordingUrl={recording_url}, CandidateID={candidate_id}, QuestionID={question_id}, NextIndex={next_question_index}")

        if not candidate_id or not question_id:
            logger.error(f"Missing candidate_id or question_id: candidate_id={candidate_id}, question_id={question_id}")
            response = VoiceResponse()
            response.say("An error occurred. Goodbye.", voice='alice')
            response.hangup()
            return Response(str(response), mimetype='application/xml', status=200)

        if recording_url:
            try:
                audio_service = AudioService()
                file_path = audio_service.download_recording(recording_url, call_sid)
                transcript = audio_service.speech_to_text(file_path)
                
                if not transcript:
                    logger.warning(f"No transcript generated for question {question_id}, saving empty transcript")
                    interview = Interview(
                        candidate_id=int(candidate_id),
                        question_id=int(question_id),
                        audio_recording_path=file_path,
                        transcript="",
                        ai_score_communication=0,
                        ai_score_technical=0,
                        ai_recommendation="No transcript",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(interview)
                    db.session.commit()
                    logger.info(f"Saved empty transcript for candidate {candidate_id}, question {question_id}")
                else:
                    question = InterviewQuestion.query.get(question_id)
                    if not question:
                        logger.error(f"Question ID {question_id} not found")
                        response = VoiceResponse()
                        response.say("An error occurred. Goodbye.", voice='alice')
                        response.hangup()
                        return Response(str(response), mimetype='application/xml', status=200)

                    try:
                        ai_service = AIService()
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
                    except Exception as e:
                        logger.error(f"Error analyzing transcript: {str(e)}")
                        interview = Interview(
                            candidate_id=int(candidate_id),
                            question_id=int(question_id),
                            audio_recording_path=file_path,
                            transcript=transcript,
                            ai_score_communication=0,
                            ai_score_technical=0,
                            ai_recommendation="Analysis failed",
                            created_at=datetime.utcnow()
                        )
                        db.session.add(interview)
                        db.session.commit()
                        logger.info(f"Saved interview with failed analysis for candidate {candidate_id}, question {question_id}")

            except Exception as e:
                logger.error(f"Error processing recording: {str(e)}")
                # Save recording with error status
                interview = Interview(
                    candidate_id=int(candidate_id),
                    question_id=int(question_id),
                    audio_recording_path=file_path if 'file_path' in locals() else None,
                    transcript="",
                    ai_score_communication=0,
                    ai_score_technical=0,
                    ai_recommendation="Processing error",
                    created_at=datetime.utcnow()
                )
                db.session.add(interview)
                db.session.commit()
                logger.info(f"Saved error record for candidate {candidate_id}, question {question_id}")

        if digits_pressed and next_question_index:
            logger.info(f"User pressed key '{digits_pressed}' for question {question_id}. Asking next question.")
            try:
                twilio_service = TwilioService()
                twiml_response = twilio_service.handle_call_flow(
                    candidate_id=candidate_id, 
                    question_index=int(next_question_index)
                )
                return Response(twiml_response, mimetype='application/xml', status=200)
            except Exception as e:
                logger.error(f"Error generating next question: {str(e)}")
                response = VoiceResponse()
                response.say("An error occurred. Goodbye.", voice='alice')
                response.hangup()
                return Response(str(response), mimetype='application/xml', status=200)
        else:
            logger.warning(f"No key pressed for question {question_id}, ending call")
            response = VoiceResponse()
            response.say("No input received. The call will now end.", voice='alice')
            response.hangup()
            candidate = Candidate.query.get(candidate_id)
            if candidate:
                candidate.status = 'completed'
                db.session.commit()
                logger.info(f"Updated candidate {candidate_id} status to completed")
                campaign = Campaign.query.get(candidate.campaign_id)
                if campaign:
                    candidates = Candidate.query.filter_by(campaign_id=campaign.id).all()
                    if all(c.status == 'completed' for c in candidates):
                        campaign.status = 'completed'
                        db.session.commit()
                        logger.info(f"Campaign {campaign.id} marked as completed")
            return Response(str(response), mimetype='application/xml', status=200)

# class RecordingHandlerResource(Resource):
#     def post(self):
#         call_sid = request.form.get('CallSid')
#         digits_pressed = request.form.get('Digits')
#         recording_url = request.form.get('RecordingUrl')
#         candidate_id = request.args.get('candidate_id')
#         question_id = request.args.get('question_id')
#         next_question_index = request.args.get('next_question_index')

#         logger.info(f"Recording handler: SID={call_sid}, Digits={digits_pressed}, RecordingUrl={recording_url}, CandidateID={candidate_id}, QuestionID={question_id}, NextIndex={next_question_index}")

#         if recording_url:
#             try:
#                 audio_service = AudioService()
#                 ai_service = AIService()
#                 file_path = audio_service.download_recording(recording_url, call_sid)
#                 transcript = audio_service.speech_to_text(file_path)
                
#                 if not transcript:
#                     logger.warning(f"No transcript generated for question {question_id}")
#                 else:
#                     question = InterviewQuestion.query.get(question_id)
#                     if not question:
#                         logger.error(f"Question ID {question_id} not found")
#                         return Response(str(VoiceResponse().say("An error occurred. Goodbye.", voice='alice').hangup()), 
#                                       mimetype='application/xml', status=200)

#                     scores = ai_service.analyze_response(transcript, question.text)
#                     interview = Interview(
#                         candidate_id=int(candidate_id),
#                         question_id=int(question_id),
#                         audio_recording_path=file_path,
#                         transcript=transcript,
#                         ai_score_communication=scores['communication_score'],
#                         ai_score_technical=scores['technical_score'],
#                         ai_recommendation=scores['recommendation'],
#                         created_at=datetime.utcnow()
#                     )
#                     db.session.add(interview)
#                     db.session.commit()
#                     logger.info(f"Saved interview record for candidate {candidate_id}, question {question_id}")
                
#             except Exception as e:
#                 logger.error(f"Error processing recording or scoring: {str(e)}")

#         if digits_pressed:
#             logger.info(f"User pressed key '{digits_pressed}' for question {question_id}. Asking next question.")
#             try:
#                 twilio_service = TwilioService()
#                 twiml_response = twilio_service.handle_call_flow(
#                     candidate_id=candidate_id, 
#                     question_index=int(next_question_index)
#                 )
#                 return Response(twiml_response, mimetype='application/xml', status=200)
#             except Exception as e:
#                 logger.error(f"Error generating next question: {str(e)}")
#                 response = VoiceResponse()
#                 response.say("An error occurred. Goodbye.", voice='alice')
#                 response.hangup()
#                 return Response(str(response), mimetype='application/xml', status=200)
#         else:
#             logger.warning("No key pressed, ending call")
#             response = VoiceResponse()
#             response.say("No input received. The call will now end.", voice='alice')
#             response.hangup()
#             return Response(str(response), mimetype='application/xml', status=200)

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

class CallStatusHandlerResource(Resource):
    def post(self):
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        candidate = Candidate.query.filter_by(call_sid=call_sid).first()

        if candidate:
            candidate.status = call_status
            try:
                db.session.commit()
                logger.info(f"Updated call status for candidate {candidate.id}: {call_status}")

                # Check if all candidates in the campaign are completed
                campaign = Campaign.query.get(candidate.campaign_id)
                if campaign:
                    candidates = Candidate.query.filter_by(campaign_id=campaign.id).all()
                    all_completed = all(c.status == 'completed' for c in candidates)
                    logger.info(f"Campaign {campaign.id} has {len(candidates)} candidates, {sum(1 for c in candidates if c.status == 'completed')} completed")
                    if all_completed:
                        campaign.status = 'completed'
                        db.session.commit()
                        logger.info(f"Campaign {campaign.id} marked as completed; all candidates finished.")
                    else:
                        logger.info(f"Campaign {campaign.id} still running; not all candidates completed.")
                else:
                    logger.warning(f"No campaign found for candidate {candidate.id}")
            except Exception as e:
                logger.error(f"Failed to commit database changes: {str(e)}")
                db.session.rollback()
                return {"message": "Failed to update status"}, 500
        else:
            logger.warning(f"No candidate found for CallSid {call_sid}")
            return {"message": "Candidate not found"}, 404

        return {"message": "Call status updated"}, 200

class RecordingStatusHandlerResource(Resource):
    def post(self):
        call_sid = request.form.get('CallSid')
        recording_status = request.form.get('RecordingStatus')
        recording_url = request.form.get('RecordingUrl')
        recording_duration = request.form.get('RecordingDuration')

        logger.info(f"Recording status: SID={call_sid}, Status={recording_status}, URL={recording_url}, Duration={recording_duration}")
        return {"message": "Recording status received"}, 200

class CandidateResultsResource(Resource):
    @jwt_required()
    def get(self, candidate_id):
        try:
            user_id = get_jwt_identity()
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                logger.error(f"Candidate ID {candidate_id} not found")
                return {"message": "Candidate not found"}, 404

            campaign = Campaign.query.get(candidate.campaign_id)
            if not campaign or campaign.user_id != int(user_id):
                logger.error(f"User {user_id} not authorized to access candidate {candidate_id}")
                return {"message": "Unauthorized access to candidate results"}, 403

            interviews = Interview.query.filter_by(candidate_id=candidate_id).join(InterviewQuestion).order_by(InterviewQuestion.question_order).all()
            interview_data = []
            for interview in interviews:
                question = InterviewQuestion.query.get(interview.question_id)
                interview_dict = interview.to_dict()
                interview_dict['question_text'] = question.text if question else ""
                interview_data.append(interview_dict)

            if interview_data:
                avg_communication = sum(i['ai_score_communication'] for i in interview_data if i['ai_score_communication'] is not None) / len(interview_data)
                avg_technical = sum(i['ai_score_technical'] for i in interview_data if i['ai_score_technical'] is not None) / len(interview_data)
                shortlisted = avg_communication >= 70 and avg_technical >= 70
            else:
                avg_communication = 0
                avg_technical = 0
                shortlisted = False

            return {
                "candidate": {
                    "id": candidate.id,
                    "name": candidate.name,
                    "phone_number": candidate.phone_number,
                    "email": candidate.email,
                    "campaign_id": candidate.campaign_id,
                    "status": candidate.status
                },
                "interviews": interview_data,
                "avg_communication_score": round(avg_communication, 1),
                "avg_technical_score": round(avg_technical, 1),
                "shortlisted": shortlisted
            }, 200

        except Exception as e:
            logger.error(f"Error retrieving candidate results for candidate {candidate_id}: {str(e)}")
            return {"message": "Internal server error"}, 500