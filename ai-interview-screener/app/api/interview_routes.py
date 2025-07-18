# # from flask import Response, request
# # from flask_restful import Resource
# # from app.models import Interview, InterviewQuestion, Candidate, Campaign
# # from app.services.audio_service import AudioService
# # from app.services.ai_service import AIService
# # from app.services.twilio_service import TwilioService
# # from app import db
# # from datetime import datetime
# # import logging
# # from twilio.twiml.voice_response import VoiceResponse

# # logger = logging.getLogger(__name__)

# # class CallHandlerResource(Resource):
# #     def post(self):
# #         candidate_id = request.args.get('candidate_id')
# #         logger.info(f"Call handler: candidate_id={candidate_id}")
        
# #         if not candidate_id:
# #             logger.error("No candidate_id provided")
# #             response = VoiceResponse()
# #             response.say("An error occurred. Goodbye.", voice='alice')
# #             response.hangup()
# #             return Response(str(response), mimetype='application/xml', status=200)
        
# #         twilio_service = TwilioService()
# #         twiml_response = twilio_service.handle_call_flow(candidate_id=candidate_id, question_index=0)
# #         return Response(twiml_response, mimetype='application/xml', status=200)

# # class RecordingHandlerResource(Resource):
# #     def post(self):
# #         call_sid = request.form.get('CallSid')
# #         digits_pressed = request.form.get('Digits')
# #         recording_url = request.form.get('RecordingUrl')
# #         candidate_id = request.args.get('candidate_id')
# #         question_id = request.args.get('question_id')
# #         next_question_index = request.args.get('next_question_index')

# #         logger.info(f"Recording handler: SID={call_sid}, Digits={digits_pressed}, RecordingUrl={recording_url}, CandidateID={candidate_id}, QuestionID={question_id}, NextIndex={next_question_index}")

# #         if recording_url:
# #             try:
# #                 audio_service = AudioService()
# #                 ai_service = AIService()
# #                 file_path = audio_service.download_recording(recording_url, call_sid)
# #                 transcript = audio_service.speech_to_text(file_path)
                
# #                 question = InterviewQuestion.query.get(question_id)
# #                 if not question:
# #                     logger.error(f"Question ID {question_id} not found")
# #                     return Response(str(VoiceResponse().say("An error occurred. Goodbye.", voice='alice').hangup()), 
# #                                   mimetype='application/xml', status=200)

# #                 if transcript:
# #                     scores = ai_service.analyze_response(transcript, question.text)
# #                     interview = Interview(
# #                         candidate_id=int(candidate_id),
# #                         question_id=int(question_id),
# #                         audio_recording_path=file_path,
# #                         transcript=transcript,
# #                         ai_score_communication=scores['communication_score'],
# #                         ai_score_technical=scores['technical_score'],
# #                         ai_recommendation=scores['recommendation'],
# #                         created_at=datetime.utcnow()
# #                     )
# #                     db.session.add(interview)
# #                     db.session.commit()
# #                     logger.info(f"Saved interview record for candidate {candidate_id}, question {question_id}")
# #                 else:
# #                     logger.warning(f"No transcript generated for question {question_id}")
                
# #             except Exception as e:
# #                 logger.error(f"Error processing recording or scoring: {str(e)}")

# #         if digits_pressed:
# #             logger.info(f"User pressed key '{digits_pressed}' for question {question_id}. Asking next question.")
# #             try:
# #                 twilio_service = TwilioService()
# #                 twiml_response = twilio_service.handle_call_flow(
# #                     candidate_id=candidate_id, 
# #                     question_index=int(next_question_index)
# #                 )
# #                 return Response(twiml_response, mimetype='application/xml', status=200)
# #             except Exception as e:
# #                 logger.error(f"Error generating next question: {str(e)}")
# #                 response = VoiceResponse()
# #                 response.say("An error occurred. Goodbye.", voice='alice')
# #                 response.hangup()
# #                 return Response(str(response), mimetype='application/xml', status=200)
# #         else:
# #             logger.warning("No key pressed, ending call")
# #             response = VoiceResponse()
# #             response.say("No input received. Goodbye.", voice='alice')
# #             response.hangup()
# #             return Response(str(response), mimetype='application/xml', status=200)

# # class CampaignResultsResource(Resource):
# #     def get(self, campaign_id):
# #         try:
# #             campaign = Campaign.query.get(campaign_id)
# #             if not campaign:
# #                 logger.error(f"Campaign ID {campaign_id} not found")
# #                 return {"message": "Campaign not found"}, 404

# #             candidates = Candidate.query.filter_by(campaign_id=campaign_id).all()
# #             results = []

# #             for candidate in candidates:
# #                 interviews = Interview.query.filter_by(candidate_id=candidate.id).all()
# #                 interview_data = [interview.to_dict() for interview in interviews]

# #                 if interview_data:
# #                     avg_communication = sum(i['ai_score_communication'] for i in interview_data if i['ai_score_communication'] is not None) / len(interview_data)
# #                     avg_technical = sum(i['ai_score_technical'] for i in interview_data if i['ai_score_technical'] is not None) / len(interview_data)
# #                     shortlisted = avg_communication >= 70 and avg_technical >= 70
# #                 else:
# #                     avg_communication = 0
# #                     avg_technical = 0
# #                     shortlisted = False

# #                 results.append({
# #                     "candidate": {
# #                         "id": candidate.id,
# #                         "name": candidate.name,
# #                         "phone_number": candidate.phone_number
# #                     },
# #                     "interviews": interview_data,
# #                     "avg_communication_score": round(avg_communication, 1),
# #                     "avg_technical_score": round(avg_technical, 1),
# #                     "shortlisted": shortlisted
# #                 })

# #             return {
# #                 "campaign": {
# #                     "id": campaign.id,
# #                     "name": campaign.name,
# #                     "job_description": campaign.job_description,
# #                     "status": campaign.status,
# #                     "created_at": campaign.created_at.isoformat()
# #                 },
# #                 "results": results
# #             }, 200

# #         except Exception as e:
# #             logger.error(f"Error retrieving campaign results: {str(e)}")
# #             return {"message": "Internal server error"}, 500


# from flask import Response, request
# from flask_restful import Resource
# from app.models import Interview, InterviewQuestion, Candidate, Campaign
# from app.services.audio_service import AudioService
# from app.services.ai_service import AIService
# from app.services.twilio_service import TwilioService
# from app import db
# from datetime import datetime
# import logging
# from twilio.twiml.voice_response import VoiceResponse

# logger = logging.getLogger(__name__)

# class CallHandlerResource(Resource):
#     def post(self):
#         candidate_id = request.args.get('candidate_id')
#         logger.info(f"Call handler: candidate_id={candidate_id}")
        
#         if not candidate_id:
#             logger.error("No candidate_id provided")
#             response = VoiceResponse()
#             response.say("An error occurred. Goodbye.", voice='alice')
#             response.hangup()
#             return Response(str(response), mimetype='application/xml', status=200)
        
#         twilio_service = TwilioService()
#         twiml_response = twilio_service.handle_call_flow(candidate_id=candidate_id, question_index=0)
#         return Response(twiml_response, mimetype='application/xml', status=200)

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
                
#                 question = InterviewQuestion.query.get(question_id)
#                 if not question:
#                     logger.error(f"Question ID {question_id} not found")
#                     return Response(str(VoiceResponse().say("An error occurred. Goodbye.", voice='alice').hangup()), 
#                                   mimetype='application/xml', status=200)

#                 if transcript:
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
#                 else:
#                     logger.warning(f"No transcript generated for question {question_id}")
                
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
#             response.say("No input received. Goodbye.", voice='alice')
#             response.hangup()
#             return Response(str(response), mimetype='application/xml', status=200)

# class CampaignResultsResource(Resource):
#     def get(self, campaign_id):
#         try:
#             campaign = Campaign.query.get(campaign_id)
#             if not campaign:
#                 logger.error(f"Campaign ID {campaign_id} not found")
#                 return {"message": "Campaign not found"}, 404

#             candidates = Candidate.query.filter_by(campaign_id=campaign_id).all()
#             results = []

#             for candidate in candidates:
#                 interviews = Interview.query.filter_by(candidate_id=candidate.id).all()
#                 interview_data = [interview.to_dict() for interview in interviews]

#                 if interview_data:
#                     avg_communication = sum(i['ai_score_communication'] for i in interview_data if i['ai_score_communication'] is not None) / len(interview_data)
#                     avg_technical = sum(i['ai_score_technical'] for i in interview_data if i['ai_score_technical'] is not None) / len(interview_data)
#                     shortlisted = avg_communication >= 70 and avg_technical >= 70
#                 else:
#                     avg_communication = 0
#                     avg_technical = 0
#                     shortlisted = False

#                 results.append({
#                     "candidate": {
#                         "id": candidate.id,
#                         "name": candidate.name,
#                         "phone_number": candidate.phone_number
#                     },
#                     "interviews": interview_data,
#                     "avg_communication_score": round(avg_communication, 1),
#                     "avg_technical_score": round(avg_technical, 1),
#                     "shortlisted": shortlisted
#                 })

#             return {
#                 "campaign": {
#                     "id": campaign.id,
#                     "name": campaign.name,
#                     "job_description": campaign.job_description,
#                     "status": campaign.status,
#                     "created_at": campaign.created_at.isoformat()
#                 },
#                 "results": results
#             }, 200

#         except Exception as e:
#             logger.error(f"Error retrieving campaign results: {str(e)}")
#             return {"message": "Internal server error"}, 500

# class CallStatusHandlerResource(Resource):
#     def post(self):
#         call_sid = request.form.get('CallSid')
#         call_status = request.form.get('CallStatus')
#         candidate = Candidate.query.filter_by(call_sid=call_sid).first()

#         if candidate:
#             candidate.status = call_status
#             db.session.commit()
#             logger.info(f"Updated call status for candidate {candidate.id}: {call_status}")
#         else:
#             logger.warning(f"No candidate found for CallSid {call_sid}")

#         return {"message": "Call status updated"}, 200

# class RecordingStatusHandlerResource(Resource):
#     def post(self):
#         call_sid = request.form.get('CallSid')
#         recording_status = request.form.get('RecordingStatus')
#         recording_url = request.form.get('RecordingUrl')
#         recording_duration = request.form.get('RecordingDuration')

#         logger.info(f"Recording status: SID={call_sid}, Status={recording_status}, URL={recording_url}, Duration={recording_duration}")
#         return {"message": "Recording status received"}, 200



from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import jwt_required
from app.models import Candidate, Interview, InterviewQuestion, Campaign
from app.services.twilio_service import TwilioService
from app.services.audio_service import AudioService
from app.services.ai_service import AIService
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

interview_bp = Blueprint('interview', __name__)
api = Api(interview_bp)

twilio_service = TwilioService()
audio_service = AudioService()
ai_service = AIService()

class CallHandlerResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('CallSid', type=str, required=True)
        parser.add_argument('To', type=str, required=True)
        parser.add_argument('candidate_id', type=int, required=True)
        args = parser.parse_args()

        logger.info(f"Call handler: candidate_id={args['candidate_id']}")
        twiml = twilio_service.handle_call(args['candidate_id'], 0)
        return {'twiml': str(twiml)}, 200

class RecordingHandlerResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('CallSid', type=str, required=True)
        parser.add_argument('RecordingSid', type=str)
        parser.add_argument('RecordingUrl', type=str)
        parser.add_argument('Digits', type=str)
        parser.add_argument('candidate_id', type=int, required=True)
        parser.add_argument('question_id', type=int, required=True)
        parser.add_argument('next_question_index', type=int, required=True)
        args = parser.parse_args()

        logger.info(f"Recording handler: SID={args['CallSid']}, Digits={args['Digits']}, RecordingUrl={args['RecordingUrl']}, CandidateID={args['candidate_id']}, QuestionID={args['question_id']}, NextIndex={args['next_question_index']}")

        file_path = None
        if args['RecordingUrl']:
            file_path = audio_service.download_recording(args['RecordingUrl'], args['CallSid'])
            transcript = audio_service.speech_to_text(file_path)
            question = InterviewQuestion.query.get(args['question_id'])
            
            if transcript:
                scores = ai_service.analyze_response(transcript, question.text)
                interview = Interview(
                    candidate_id=args['candidate_id'],
                    question_id=args['question_id'],
                    audio_recording_path=file_path,
                    transcript=transcript,
                    ai_score_communication=scores['communication_score'],
                    ai_score_technical=scores['technical_score'],
                    ai_recommendation=scores['recommendation'],
                    created_at=datetime.utcnow()
                )
                db.session.add(interview)
                db.session.commit()
                logger.info(f"Saved interview record for candidate {args['candidate_id']}, question {args['question_id']}")
            else:
                logger.warning(f"No transcript generated for question {args['question_id']}")
                interview = Interview(
                    candidate_id=args['candidate_id'],
                    question_id=args['question_id'],
                    audio_recording_path=file_path,
                    transcript="No transcript available",
                    ai_score_communication=0,
                    ai_score_technical=0,
                    ai_recommendation="Reject",
                    created_at=datetime.utcnow()
                )
                db.session.add(interview)
                db.session.commit()
                logger.info(f"Saved partial interview record for candidate {args['candidate_id']}, question {args['question_id']}")

        if args['Digits']:
            logger.info(f"User pressed key '{args['Digits']}' for question {args['question_id']}. Asking next question.")
            twiml = twilio_service.handle_call(args['candidate_id'], args['next_question_index'])
            return {'twiml': str(twiml)}, 200
        else:
            logger.warning("No key pressed, ending call")
            twiml = twilio_service.end_call()
            return {'twiml': str(twiml)}, 200

class RecordingStatusResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('CallSid', type=str, required=True)
        parser.add_argument('RecordingStatus', type=str, required=True)
        parser.add_argument('RecordingUrl', type=str)
        parser.add_argument('RecordingDuration', type=str)
        args = parser.parse_args()

        logger.info(f"Recording status: SID={args['CallSid']}, Status={args['RecordingStatus']}, URL={args['RecordingUrl']}, Duration={args['RecordingDuration']}")

        if args['RecordingStatus'] == 'completed':
            candidate = Candidate.query.filter_by(call_sid=args['CallSid']).first()
            if candidate:
                candidate.call_status = 'completed'
                db.session.commit()
                logger.info(f"Updated call status for candidate {candidate.id}: completed")

        return {}, 200

class CandidateResultsResource(Resource):
    def get(self, candidate_id):
        try:
            candidate = Candidate.query.get_or_404(candidate_id)
            interviews = (
                db.session.query(Interview, InterviewQuestion.text)
                .join(InterviewQuestion, Interview.question_id == InterviewQuestion.id)
                .filter(Interview.candidate_id == candidate_id)
                .all()
            )
            
            if not interviews:
                logger.info(f"No interview results found for candidate {candidate_id}")
                return {"message": f"No results found for candidate {candidate_id}"}, 404

            results = []
            total_communication_score = 0
            total_technical_score = 0
            for interview, question_text in interviews:
                results.append({
                    "question_id": interview.question_id,
                    "question_text": question_text,
                    "transcript": interview.transcript,
                    "audio_recording_path": interview.audio_recording_path,
                    "communication_score": interview.ai_score_communication,
                    "technical_score": interview.ai_score_technical,
                    "recommendation": interview.ai_recommendation,
                    "created_at": interview.created_at.isoformat()
                })
                total_communication_score += interview.ai_score_communication
                total_technical_score += interview.ai_score_technical

            count = len(interviews)
            avg_communication_score = total_communication_score / count if count > 0 else 0
            avg_technical_score = total_technical_score / count if count > 0 else 0
            overall_recommendation = "Consider" if avg_technical_score >= 50 and avg_communication_score >= 50 else "Reject"

            response = {
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "candidate_phone": candidate.phone_number,
                "results": results,
                "average_communication_score": round(avg_communication_score, 2),
                "average_technical_score": round(avg_technical_score, 2),
                "overall_recommendation": overall_recommendation
            }

            logger.info(f"Retrieved results for candidate {candidate_id}")
            return response, 200

        except Exception as e:
            logger.error(f"Error retrieving results for candidate {candidate_id}: {str(e)}")
            return {"message": f"Error retrieving results: {str(e)}"}, 500

class CampaignResultsResource(Resource):
    @jwt_required()
    def get(self, campaign_id):
        try:
            campaign = Campaign.query.get_or_404(campaign_id)
            candidates = Candidate.query.filter_by(campaign_id=campaign_id).all()
            
            if not candidates:
                logger.info(f"No candidates found for campaign {campaign_id}")
                return {
                    "campaign": {
                        "id": campaign.id,
                        "name": campaign.name,
                        "job_description": campaign.job_description,
                        "status": campaign.status,
                        "created_at": campaign.created_at.isoformat()
                    },
                    "results": []
                }, 200

            results = []
            for candidate in candidates:
                interviews = (
                    db.session.query(Interview, InterviewQuestion.text)
                    .join(InterviewQuestion, Interview.question_id == InterviewQuestion.id)
                    .filter(Interview.candidate_id == candidate.id)
                    .all()
                )
                
                interview_results = []
                total_communication_score = 0
                total_technical_score = 0
                for interview, question_text in interviews:
                    interview_results.append({
                        "id": interview.id,
                        "question_id": interview.question_id,
                        "question_text": question_text,
                        "transcript": interview.transcript,
                        "audio_recording_path": interview.audio_recording_path,
                        "ai_score_communication": interview.ai_score_communication,
                        "ai_score_technical": interview.ai_score_technical,
                        "ai_recommendation": interview.ai_recommendation,
                        "created_at": interview.created_at.isoformat()
                    })
                    total_communication_score += interview.ai_score_communication
                    total_technical_score += interview.ai_score_technical

                count = len(interview_results)
                avg_communication_score = total_communication_score / count if count > 0 else 0
                avg_technical_score = total_technical_score / count if count > 0 else 0
                shortlisted = avg_technical_score >= 50 and avg_communication_score >= 50

                results.append({
                    "candidate": {
                        "id": candidate.id,
                        "name": candidate.name,
                        "phone_number": candidate.phone_number
                    },
                    "interviews": interview_results,
                    "avg_communication_score": round(avg_communication_score, 2),
                    "avg_technical_score": round(avg_technical_score, 2),
                    "shortlisted": shortlisted
                })

            response = {
                "campaign": {
                    "id": campaign.id,
                    "name": campaign.name,
                    "job_description": campaign.job_description,
                    "status": campaign.status,
                    "created_at": campaign.created_at.isoformat()
                },
                "results": results
            }

            logger.info(f"Retrieved results for campaign {campaign_id}")
            return response, 200

        except Exception as e:
            logger.error(f"Error retrieving results for campaign {campaign_id}: {str(e)}")
            return {"message": f"Error retrieving results: {str(e)}"}, 500

