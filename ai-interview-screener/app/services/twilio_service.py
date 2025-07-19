# import logging
# from flask import current_app
# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse, Say, Record, Gather, Hangup
# from sqlalchemy.orm import joinedload
# from app.models import Candidate, InterviewQuestion
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

#     def handle_call_flow(self, candidate_id, question_index=0):
#         logger.info(f"Handling call flow for candidate_id={candidate_id}, question_index={question_index}")
#         candidate = Candidate.query.options(joinedload(Candidate.campaign)).get(candidate_id)
#         if not candidate:
#             logger.error(f"Candidate ID {candidate_id} not found")
#             response = VoiceResponse()
#             response.say("An application error has occurred. Goodbye.", voice='alice')
#             response.hangup()
#             return str(response)

#         response = VoiceResponse()
#         questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()
#         if not questions:
#             logger.error(f"No questions found for campaign_id={candidate.campaign_id}")
#             response.say("No questions available. Goodbye.", voice='alice')
#             response.hangup()
#             return str(response)

#         if question_index == 0:
#             response.say(f"Hello {candidate.name}. This is an automated interview. Please answer each question clearly, then press any key, such as 1, to continue to the next question.", voice='alice')
#             response.pause(length=2)

#         if question_index < len(questions):
#             current_question = questions[question_index]
#             response.say(current_question.text, voice='alice')
#             response.say("Please provide your answer, then press any key, such as 1, to continue.", voice='alice')
            
#             recording_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
#             response.record(
#                 action=recording_url,
#                 method='POST',
#                 max_length=60,
#                 timeout=5,
#                 play_beep=True,
#                 recording_status_callback=f"{self.base_url}/api/voice/recording_status",
#                 recording_status_callback_method='POST'
#             )
            
#             gather = response.gather(input='dtmf', num_digits=1, action=recording_url, method='POST', timeout=15)
#             gather.say("Please press any key, such as 1, to continue.", voice='alice')
#             gather.pause(length=2)
#             gather.say("Still waiting for your input...", voice='alice')
#             response.say("No input received. The call will now end.", voice='alice')
#             response.hangup()
#         else:
#             response.say("Thank you for completing the interview. Goodbye.", voice='alice')
#             response.hangup()

#         logger.info(f"TwiML generated: {str(response)}")
#         return str(response)

import logging
from flask import current_app
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say, Record, Gather
from sqlalchemy.orm import joinedload
from app.models import Candidate, InterviewQuestion, Campaign
from app import db

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        self.auth_token = current_app.config['TWILIO_AUTH_TOKEN']
        self.from_number = current_app.config['TWILIO_PHONE_NUMBER']
        self.base_url = current_app.config['BASE_URL']
        self.client = Client(self.account_sid, self.auth_token)
        logger.info("TwilioService initialized")

    def start_campaign_calls(self, campaign):
        """Initiate calls for all candidates in a campaign."""
        if not campaign:
            logger.error("No campaign provided for start_campaign_calls")
            return []

        call_results = []
        for candidate in campaign.candidates:
            try:
                handler_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}"
                status_callback_url = f"{self.base_url}/api/voice/status"
                
                logger.info(f"Initiating call for candidate {candidate.id} to {candidate.phone_number}")
                call = self.client.calls.create(
                    url=handler_url,
                    to=candidate.phone_number,
                    from_=self.from_number,
                    status_callback=status_callback_url,
                    status_callback_method='POST'
                )
                candidate.status = 'initiated'
                candidate.call_sid = call.sid
                call_results.append({
                    'candidate_id': candidate.id,
                    'call_sid': call.sid,
                    'status': 'initiated'
                })
                logger.info(f"Call initiated for candidate {candidate.id}, call_sid={call.sid}")
            except Exception as e:
                logger.error(f"Failed to initiate call for candidate {candidate.id}: {str(e)}")
                call_results.append({
                    'candidate_id': candidate.id,
                    'call_sid': None,
                    'status': 'failed',
                    'error': str(e)
                })
                candidate.status = 'failed'
                candidate.call_sid = None

        try:
            db.session.commit()
            logger.info(f"Started calls for campaign {campaign.id} with {len(call_results)} candidates")
        except Exception as e:
            logger.error(f"Error committing campaign {campaign.id} calls to database: {str(e)}")
            db.session.rollback()

        return call_results

    def handle_call_flow(self, candidate_id, question_index=0):
        """Generate TwiML for call flow based on candidate and question index."""
        logger.info(f"Handling call flow for candidate_id={candidate_id}, question_index={question_index}")
        
        if not candidate_id:
            logger.error("No candidate_id provided")
            response = VoiceResponse()
            response.say("An application error has occurred. Goodbye.", voice='alice')
            response.hangup()
            return str(response)

        candidate = Candidate.query.options(joinedload(Candidate.campaign)).get(candidate_id)
        if not candidate:
            logger.error(f"Candidate ID {candidate_id} not found")
            response = VoiceResponse()
            response.say("An application error has occurred. Goodbye.", voice='alice')
            response.hangup()
            return str(response)

        response = VoiceResponse()
        questions = InterviewQuestion.query.filter_by(campaign_id=candidate.campaign_id).order_by(InterviewQuestion.question_order).all()
        if not questions:
            logger.error(f"No questions found for campaign_id={candidate.campaign_id}")
            response.say("No questions available. Goodbye.", voice='alice')
            response.hangup()
            candidate.status = 'completed'
            db.session.commit()
            logger.info(f"Updated candidate {candidate_id} status to completed due to no questions")
            campaign = Campaign.query.get(candidate.campaign_id)
            if campaign:
                candidates = Candidate.query.filter_by(campaign_id=campaign.id).all()
                if all(c.status in ['completed', 'failed'] for c in candidates):
                    campaign.status = 'completed'
                    db.session.commit()
                    logger.info(f"Campaign {campaign.id} marked as completed")
            return str(response)

        if question_index == 0:
            response.say(
                f"Hello {candidate.name}. This is an automated interview. Please answer each question clearly, then press any key, such as 1, to continue to the next question.",
                voice='alice'
            )
            response.pause(length=2)

        if question_index < len(questions):
            current_question = questions[question_index]
            response.say(current_question.text, voice='alice')
            response.say("Please provide your answer after the beep.", voice='alice')
            
            recording_url = f"{self.base_url}/api/voice/recording_handler?candidate_id={candidate.id}&question_id={current_question.id}&next_question_index={question_index + 1}"
            response.record(
                action=recording_url,
                method='POST',
                max_length=60,
                timeout=10,
                play_beep=True,
                recording_status_callback=f"{self.base_url}/api/voice/recording_status",
                recording_status_callback_method='POST'
            )
            
            # Separate DTMF gathering into a new action
            gather_url = f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}&question_index={question_index + 1}"
            gather = response.gather(input='dtmf', num_digits=1, action=gather_url, method='POST', timeout=15)
            gather.say("Please press any key, such as 1, to continue.", voice='alice')
            gather.pause(length=2)
            gather.say("Still waiting for your input...", voice='alice')
            
            # Redirect to end call if no input
            response.redirect(
                url=f"{self.base_url}/api/voice/call_handler?candidate_id={candidate.id}&question_index={question_index + 1}",
                method='POST'
            )
        else:
            response.say("Thank you for completing the interview. Goodbye.", voice='alice')
            response.hangup()
            candidate.status = 'completed'
            db.session.commit()
            logger.info(f"Updated candidate {candidate_id} status to completed")
            campaign = Campaign.query.get(candidate.campaign_id)
            if campaign:
                candidates = Candidate.query.filter_by(campaign_id=campaign.id).all()
                if all(c.status in ['completed', 'failed'] for c in candidates):
                    campaign.status = 'completed'
                    db.session.commit()
                    logger.info(f"Campaign {campaign.id} marked as completed")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"TwiML generated: {str(response)}")
        else:
            logger.info(f"TwiML generated for candidate {candidate_id}, question_index {question_index}")

        return str(response)