# # app/services/twilio_service.py

# import logging
# from flask import current_app
# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse, Say, Record, Hangup, Pause
# from sqlalchemy.orm import joinedload
# from app.models import Candidate, InterviewQuestion, Interview
# from app import db

# logger = logging.getLogger(__name__)

# class TwilioService:
#     def __init__(self):
#         self.account_sid = current_app.config['TWILIO_ACCOUNT_SID']
#         self.auth_token = current_app.config['TWILIO_AUTH_TOKEN']
#         self.from_number = current_app.config['TWILIO_PHONE_NUMBER']
#         self.base_url = current_app.config['BASE_URL']
#         self.client = Client(self.account_sid, self.auth_token)

#     def start_campaign_calls(self, campaign):
#         call_results = []
#         for candidate in campaign.candidates:
#             handler_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}"
#             status_callback_url = f"{self.base_url}/api/voice/status"
            
#             call = self.client.calls.create(
#                 url=handler_url,
#                 to=candidate.phone_number,
#                 from_=self.from_number,
#                 status_callback=status_callback_url,
#                 status_callback_method='POST'
#             )
#             candidate.status = 'initiated'
#             candidate.call_sid = call.sid
#             call_results.append({'candidate_id': candidate.id, 'call_sid': call.sid, 'status': 'initiated'})
        
#         db.session.commit()
#         return call_results

#     # def handle_call_flow(self, candidate_id, question_index=0):
#     #     logger.info(f"Handling call flow for candidate_id={candidate_id}, question_index={question_index}")
#     #     candidate = Candidate.query.options(joinedload(Candidate.campaign)).get(candidate_id)
#     #     if not candidate:
#     #         logger.error(f"Candidate ID {candidate_id} not found")
#     #         response = VoiceResponse()
#     #         response.say("An application error has occurred. Goodbye.", voice='alice')
#     #         response.hangup()
#     #         return response

#     #     response = VoiceResponse()
#     #     questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()
#     #     if not questions:
#     #         logger.error(f"No questions found for campaign_id={candidate.campaign_id}")
#     #         response.say("No questions available. Goodbye.", voice='alice')
#     #         response.hangup()
#     #         return response

#     #     if question_index == 0:
#     #         response.say(f"Hello {candidate.name}. This is a test call. After each question, please press any key to continue.", voice='alice')
#     #         response.pause(length=1)

#     #     if question_index < len(questions):
#     #         current_question = questions[question_index]
#     #         response.say(current_question.text, voice='alice')
#     #         response.say("Please press any key to continue.", voice='alice')
            
#     #         gather_handler_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
            
#     #         gather = response.gather(input='dtmf', num_digits=1, action=gather_handler_url, method='POST', timeout=10)
#     #         gather.say("Waiting for your input...", voice='alice')
#     #         response.say("No input received. Goodbye.", voice='alice')
#     #         response.hangup()
#     #     else:
#     #         response.say("Thank you for completing the test. Goodbye.", voice='alice')
#     #         response.hangup()

#     #     logger.info(f"TwiML generated: {str(response)}")
#     #     return str(response)  # Return plain string

#     def handle_call_flow(self, candidate_id, question_index=0):
#         logger.info(f"Handling call flow for candidate_id={candidate_id}, question_index={question_index}")
#         candidate = Candidate.query.options(joinedload(Candidate.campaign)).get(candidate_id)
#         if not candidate:
#             logger.error(f"Candidate ID {candidate_id} not found")
#             response = VoiceResponse()
#             response.say("An application error has occurred. Goodbye.", voice='alice')
#             response.hangup()
#             return response

#         response = VoiceResponse()
#         questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()
#         if not questions:
#             logger.error(f"No questions found for campaign_id={candidate.campaign_id}")
#             response.say("No questions available. Goodbye.", voice='alice')
#             response.hangup()
#             return response

#         if question_index == 0:
#             response.say(f"Hello {candidate.name}. This is a test call. After each question, please provide your answer, then press any key to continue.", voice='alice')
#             response.pause(length=1)

#         if question_index < len(questions):
#             current_question = questions[question_index]
#             response.say(current_question.text, voice='alice')
#             response.say("Please provide your answer, then press any key to continue.", voice='alice')
            
#             # Add Record verb to capture the spoken answer
#             recording_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
#             response.record(
#                 action=recording_url,
#                 method='POST',
#                 max_length=60,  # Limit answer to 60 seconds
#                 timeout=5,      # Wait 5 seconds for the candidate to start speaking
#                 play_beep=True, # Play a beep to signal the start of recording
#                 recording_status_callback=f"{self.base_url}/api/voice/recording_status",
#                 recording_status_callback_method='POST'
#             )
            
#             # Gather DTMF input to proceed to the next question
#             gather = response.gather(input='dtmf', num_digits=1, action=recording_url, method='POST', timeout=10)
#             gather.say("Waiting for your input...", voice='alice')
#             response.say("No input received. Goodbye.", voice='alice')
#             response.hangup()
#         else:
#             response.say("Thank you for completing the test. Goodbye.", voice='alice')
#             response.hangup()

#         logger.info(f"TwiML generated: {str(response)}")
#         return str(response)


from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from flask import current_app
from app.models import Candidate, InterviewQuestion
from app import db
import logging
import os

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        self.client = Client(account_sid, auth_token)
        self.base_url = os.environ.get('APP_BASE_URL', 'http://13.201.187.228:5000')

    def initiate_call(self, candidate_id):
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            return None

        try:
            call = self.client.calls.create(
                to=candidate.phone_number,
                from_=self.from_number,
                url=f"{self.base_url}/api/voice/call_handler",
                method='POST',
                status_callback=f"{self.base_url}/api/voice/recording_status",
                status_callback_method='POST',
                status_callback_event=['completed']
            )
            candidate.call_sid = call.sid
            db.session.commit()
            logger.info(f"Initiated call for candidate {candidate_id}, CallSid: {call.sid}")
            return call.sid
        except Exception as e:
            logger.error(f"Failed to initiate call for candidate {candidate_id}: {str(e)}")
            return None

    def handle_call(self, candidate_id, question_index):
        response = VoiceResponse()
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            response.say("Sorry, we could not find your information. Goodbye.")
            response.hangup()
            return response

        # Fetch questions for the candidate's campaign, ordered by question_order
        questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()
        logger.debug(f"Questions for campaign {candidate.campaign_id}: {[q.to_dict() for q in questions]}")

        if not questions:
            logger.warning(f"No questions found for campaign {candidate.campaign_id}")
            response.say("No questions are available for this campaign. Goodbye.")
            response.hangup()
            return response

        if question_index >= len(questions):
            logger.info(f"All questions completed for candidate {candidate_id}")
            response.say("Thank you for completing the interview. Goodbye.")
            response.hangup()
            return response

        question = questions[question_index]
        logger.info(f"Asking question {question.id} for candidate {candidate_id}: {question.text}")

        # Prompt the candidate with the question
        response.say(f"Question {question_index + 1}: {question.text}")
        response.say("Please record your answer after the beep, then press any key to continue.")

        # Record the response
        response.record(
            action=f"{self.base_url}/api/voice/recording_handler",
            method='POST',
            max_length=120,  # Increased to 120 seconds
            play_beep=True,
            recording_status_callback=f"{self.base_url}/api/voice/recording_status",
            recording_status_callback_method='POST',
            timeout=5,
            transcribe=False
        )

        # Pass candidate_id, question_id, and next_question_index to recording_handler
        response.append(
            f"<Pass candidate_id='{candidate_id}' question_id='{question.id}' next_question_index='{question_index + 1}' />"
        )

        return response

    def end_call(self):
        response = VoiceResponse()
        response.say("Thank you for participating. Goodbye.")
        response.hangup()
        logger.info("Call ended")
        return response