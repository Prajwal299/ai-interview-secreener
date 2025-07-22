

# import logging
# from flask import request
# from flask_restful import Resource, reqparse
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from app.models import Campaign, Candidate, InterviewQuestion, UploadedCSV
# from app.services.ai_service import AIService
# from app.services.twilio_service import TwilioService
# from app import db
# import csv
# import io

# logger = logging.getLogger(__name__)

# class CampaignListResource(Resource):
#     @jwt_required()
#     def get(self):
#         user_id = get_jwt_identity()
#         campaigns = Campaign.query.filter_by(user_id=user_id).all()
#         return {'campaigns': [campaign.to_dict() for campaign in campaigns]}, 200
    
#     @jwt_required()
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('name', type=str, required=True, help='Campaign name is required')
#         parser.add_argument('job_description', type=str, required=True, help='Job description is required')
#         args = parser.parse_args()
        
#         user_id = get_jwt_identity()
        
#         campaign = Campaign(
#             name=args['name'],
#             job_description=args['job_description'],
#             user_id=user_id
#         )
        
#         db.session.add(campaign)
#         db.session.commit()
        
#         ai_service = AIService()
#         questions = ai_service.generate_questions(args['job_description'])
        
#         for i, question_text in enumerate(questions, 1):
#             question = InterviewQuestion(
#                 text=question_text,
#                 campaign_id=campaign.id,
#                 question_order=i
#             )
#             db.session.add(question)
        
#         db.session.commit()
        
#         return {'message': 'Campaign created successfully', 'campaign': campaign.to_dict()}, 201

# class CampaignResource(Resource):
#     @jwt_required()
#     def get(self, campaign_id):
#         user_id = get_jwt_identity()
#         campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
#         if not campaign:
#             return {'message': 'Campaign not found'}, 404
        
#         campaign_data = campaign.to_dict()
#         campaign_data['candidates'] = [candidate.to_dict() for candidate in campaign.candidates]
#         campaign_data['questions'] = [question.to_dict() for question in campaign.questions]
        
#         return {'campaign': campaign_data}, 200

# class CandidateUploadResource(Resource):
#     @jwt_required()
#     def post(self, campaign_id):
#         user_id = get_jwt_identity()
#         campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
#         if not campaign:
#             logger.warning(f"User {user_id} tried to upload candidates to non-existent campaign {campaign_id}")
#             return {'message': 'Campaign not found'}, 404
        
#         if 'file' not in request.files:
#             return {'message': 'No file provided'}, 400
        
#         file = request.files['file']
#         if file.filename == '':
#             return {'message': 'No file selected'}, 400
        
#         if not file.filename.endswith('.csv'):
#             return {'message': 'File must be a CSV'}, 400
        
#         csv_content = file.read()
#         uploaded_csv = UploadedCSV(
#             filename=file.filename,
#             content=csv_content,
#             user_id=user_id
#         )
#         db.session.add(uploaded_csv)
#         db.session.commit()
        
#         stream = io.StringIO(csv_content.decode("UTF8"), newline=None)
#         csv_reader = csv.DictReader(stream)
        
#         candidates_added = 0
#         logger.info(f"Processing CSV upload for campaign {campaign_id}")
        
#         for row in csv_reader:
#             name = row.get('name')
#             phone_number = row.get('phone_number')
#             if name and phone_number:
#                 candidate = Candidate(
#                     name=name,
#                     phone_number=phone_number,
#                     email=row.get('email', ''),
#                     campaign_id=campaign_id
#                 )
#                 db.session.add(candidate)
#                 candidates_added += 1
#                 logger.debug(f"Adding candidate: {name}, {phone_number} to campaign {campaign_id}")
#             else:
#                 logger.warning(f"Skipping row in CSV due to missing 'name' or 'phone_number': {row}")
        
#         db.session.commit()
#         logger.info(f"Successfully added {candidates_added} candidates to campaign {campaign_id}")
        
#         return {
#             'message': f'{candidates_added} candidates added successfully',
#             'csv_id': uploaded_csv.id
#         }, 201

# class StartCampaignResource(Resource):
#     @jwt_required()
#     def post(self, campaign_id):
#         user_id = get_jwt_identity()
#         campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
#         if not campaign:
#             logger.warning(f"User {user_id} tried to start non-existent campaign {campaign_id}")
#             return {'message': 'Campaign not found'}, 404
        
#         if campaign.status != 'created':
#             logger.warning(f"Attempt to start campaign {campaign_id} which is not in 'created' status (current: {campaign.status})")
#             return {'message': f'Campaign is not in created status (is {campaign.status})'}, 400
        
#         candidate_count = len(campaign.candidates)
#         logger.info(f"Starting campaign {campaign_id}. Found {candidate_count} associated candidates.")

#         if candidate_count == 0:
#             logger.error(f"Campaign {campaign_id} cannot start because it has no candidates.")
#             return {'message': 'Cannot start campaign: No candidates have been uploaded.'}, 400
            
#         campaign.status = 'running'
#         db.session.commit()
        
#         try:
#             twilio_service = TwilioService()
#             results = twilio_service.start_campaign_calls(campaign)
#             return {'message': 'Campaign started successfully', 'call_results': results}, 200
#         except Exception as e:
#             logger.critical(f"A critical error occurred while starting campaign {campaign_id}: {e}", exc_info=True)
#             campaign.status = 'failed'
#             db.session.commit()
#             return {'message': 'An internal error occurred while trying to start the campaign.'}, 500

# class UploadedCSVListResource(Resource):
#     @jwt_required()
#     def get(self):
#         user_id = get_jwt_identity()
#         csvs = UploadedCSV.query.filter_by(user_id=user_id).all()
#         return {'csvs': [csv.to_dict() for csv in csvs]}, 200


import logging
from flask import request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Campaign, Candidate, InterviewQuestion, UploadedCSV
from app.services.ai_service import AIService
from app.services.twilio_service import TwilioService
from app import db
import csv
import io

logger = logging.getLogger(__name__)

class CampaignListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        campaigns = Campaign.query.filter_by(user_id=user_id).all()
        return {'campaigns': [campaign.to_dict() for campaign in campaigns]}, 200
    
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help='Campaign name is required')
        parser.add_argument('job_description', type=str, required=True, help='Job description is required')
        args = parser.parse_args()
        
        user_id = get_jwt_identity()
        
        campaign = Campaign(
            name=args['name'],
            job_description=args['job_description'],
            user_id=user_id
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        ai_service = AIService()
        questions = ai_service.generate_questions(args['job_description'])
        
        for i, question_text in enumerate(questions, 1):
            question = InterviewQuestion(
                text=question_text,
                campaign_id=campaign.id,
                question_order=i
            )
            db.session.add(question)
        
        db.session.commit()
        
        return {'message': 'Campaign created successfully', 'campaign': campaign.to_dict()}, 201

class CampaignResource(Resource):
    @jwt_required()
    def get(self, campaign_id):
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return {'message': 'Campaign not found'}, 404
        
        campaign_data = campaign.to_dict()
        campaign_data['candidates'] = [candidate.to_dict() for candidate in campaign.candidates]
        campaign_data['questions'] = [question.to_dict() for question in campaign.questions]
        
        return {'campaign': campaign_data}, 200

class CandidateUploadResource(Resource):
    @jwt_required()
    def post(self, campaign_id):
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            logger.warning(f"User {user_id} tried to upload candidates to non-existent campaign {campaign_id}")
            return {'message': 'Campaign not found'}, 404
        
        if 'file' not in request.files:
            return {'message': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'message': 'No file selected'}, 400
        
        if not file.filename.endswith('.csv'):
            return {'message': 'File must be a CSV'}, 400
        
        csv_content = file.read()
        uploaded_csv = UploadedCSV(
            filename=file.filename,
            content=csv_content,
            user_id=user_id
        )
        db.session.add(uploaded_csv)
        db.session.commit()
        
        stream = io.StringIO(csv_content.decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        candidates_added = 0
        logger.info(f"Processing CSV upload for campaign {campaign_id}")
        
        for row in csv_reader:
            name = row.get('name')
            phone_number = row.get('phone_number')
            if name and phone_number:
                candidate = Candidate(
                    name=name,
                    phone_number=phone_number,
                    email=row.get('email', ''),
                    campaign_id=campaign_id
                )
                db.session.add(candidate)
                candidates_added += 1
                logger.debug(f"Adding candidate: {name}, {phone_number} to campaign {campaign_id}")
            else:
                logger.warning(f"Skipping row in CSV due to missing 'name' or 'phone_number': {row}")
        
        db.session.commit()
        logger.info(f"Successfully added {candidates_added} candidates to campaign {campaign_id}")
        
        return {
            'message': f'{candidates_added} candidates added successfully',
            'csv_id': uploaded_csv.id
        }, 201

class StartCampaignResource(Resource):
    @jwt_required()
    def post(self, campaign_id):
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            logger.warning(f"User {user_id} tried to start non-existent campaign {campaign_id}")
            return {'message': 'Campaign not found'}, 404
        
        if campaign.status != 'created':
            logger.warning(f"Attempt to start campaign {campaign_id} which is not in 'created' status (current: {campaign.status})")
            return {'message': f'Campaign is not in created status (is {campaign.status})'}, 400
        
        # Check for csv_id in request body
        data = request.get_json() or {}
        csv_id = data.get('csv_id')
        candidates_added = 0
        
        if csv_id:
            # Load CSV and associate candidates
            uploaded_csv = UploadedCSV.query.filter_by(id=csv_id, user_id=user_id).first()
            if not uploaded_csv:
                logger.warning(f"User {user_id} selected non-existent or unauthorized CSV ID {csv_id}")
                return {'message': 'Selected CSV not found or unauthorized'}, 404
            
            # Check if candidates already exist for this campaign to avoid duplicates
            existing_candidates = Candidate.query.filter_by(campaign_id=campaign_id).count()
            if existing_candidates > 0:
                logger.info(f"Campaign {campaign_id} already has {existing_candidates} candidates. Using existing candidates.")
            else:
                # Parse CSV content
                stream = io.StringIO(uploaded_csv.content.decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                if not {'name', 'phone_number'}.issubset(csv_reader.fieldnames):
                    logger.error(f"CSV ID {csv_id} missing required columns 'name' or 'phone_number'")
                    return {'message': "CSV must contain 'name' and 'phone_number' columns"}, 400
                
                for row in csv_reader:
                    name = row.get('name')
                    phone_number = row.get('phone_number')
                    if name and phone_number:
                        candidate = Candidate(
                            name=name,
                            phone_number=phone_number,
                            email=row.get('email', ''),
                            campaign_id=campaign_id
                        )
                        db.session.add(candidate)
                        candidates_added += 1
                        logger.debug(f"Adding candidate: {name}, {phone_number} to campaign {campaign_id} from CSV {csv_id}")
                    else:
                        logger.warning(f"Skipping row in CSV ID {csv_id} due to missing 'name' or 'phone_number': {row}")
                
                db.session.commit()
                logger.info(f"Added {candidates_added} candidates from CSV ID {csv_id} to campaign {campaign_id}")
        
        # Check candidate count after processing CSV
        candidate_count = len(campaign.candidates)
        logger.info(f"Starting campaign {campaign_id}. Found {candidate_count} associated candidates.")

        if candidate_count == 0:
            logger.error(f"Campaign {campaign_id} cannot start because it has no candidates.")
            return {'message': 'Cannot start campaign: No candidates have been uploaded.'}, 400
            
        campaign.status = 'running'
        db.session.commit()
        
        try:
            twilio_service = TwilioService()
            results = twilio_service.start_campaign_calls(campaign)
            return {'message': 'Campaign started successfully', 'call_results': results}, 200
        except Exception as e:
            logger.critical(f"A critical error occurred while starting campaign {campaign_id}: {e}", exc_info=True)
            campaign.status = 'failed'
            db.session.commit()
            return {'message': 'An internal error occurred while trying to start the campaign.'}, 500

class UploadedCSVListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        csvs = UploadedCSV.query.filter_by(user_id=user_id).all()
        return {'csvs': [csv.to_dict() for csv in csvs]}, 200
    


class CampaignQuestionsResource(Resource):
    @jwt_required()
    def get(self, campaign_id):
        """
        Fetch all questions for a specific campaign
        
        Args:
            campaign_id (int): The ID of the campaign
            
        Returns:
            JSON response with questions or error message
        """
        try:
            user_id = get_jwt_identity()
            
            # Verify that the campaign exists and belongs to the authenticated user
            campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
            
            if not campaign:
                logger.warning(f"User {user_id} tried to access questions for non-existent or unauthorized campaign {campaign_id}")
                return {'message': 'Campaign not found or unauthorized access'}, 404
            
            # Fetch all questions for the campaign, ordered by question_order
            questions = InterviewQuestion.query.filter_by(campaign_id=campaign_id)\
                                             .order_by(InterviewQuestion.question_order)\
                                             .all()
            
            if not questions:
                logger.info(f"No questions found for campaign {campaign_id}")
                return {
                    'message': 'No questions found for this campaign',
                    'campaign_id': campaign_id,
                    'campaign_name': campaign.name,
                    'questions': []
                }, 200
            
            # Convert questions to dictionary format
            questions_data = [question.to_dict() for question in questions]
            
            logger.info(f"Successfully retrieved {len(questions_data)} questions for campaign {campaign_id}")
            
            return {
                'message': f'Successfully retrieved {len(questions_data)} questions',
                'campaign_id': campaign_id,
                'campaign_name': campaign.name,
                'campaign_status': campaign.status,
                'questions_count': len(questions_data),
                'questions': questions_data
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching questions for campaign {campaign_id}: {str(e)}", exc_info=True)
            return {'message': 'An internal error occurred while fetching questions'}, 500

# Alternative endpoint to get questions with additional filtering options
class CampaignQuestionsAdvancedResource(Resource):
    @jwt_required()
    def get(self, campaign_id):
        """
        Fetch questions for a campaign with optional filtering and pagination
        
        Query parameters:
            - limit: Maximum number of questions to return
            - offset: Number of questions to skip
            - order_by: Field to order by (question_order, created_at, text)
            - order_direction: asc or desc
        """
        try:
            from flask import request
            
            user_id = get_jwt_identity()
            
            # Verify campaign access
            campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
            
            if not campaign:
                return {'message': 'Campaign not found or unauthorized access'}, 404
            
            # Get query parameters
            limit = request.args.get('limit', type=int, default=None)
            offset = request.args.get('offset', type=int, default=0)
            order_by = request.args.get('order_by', default='question_order')
            order_direction = request.args.get('order_direction', default='asc')
            
            # Validate order_by parameter
            valid_order_fields = ['question_order', 'created_at', 'text', 'id']
            if order_by not in valid_order_fields:
                return {'message': f'Invalid order_by field. Must be one of: {valid_order_fields}'}, 400
            
            # Build query
            query = InterviewQuestion.query.filter_by(campaign_id=campaign_id)
            
            # Apply ordering
            order_field = getattr(InterviewQuestion, order_by)
            if order_direction.lower() == 'desc':
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field.asc())
            
            # Apply pagination
            if offset > 0:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            questions = query.all()
            
            # Get total count for pagination info
            total_count = InterviewQuestion.query.filter_by(campaign_id=campaign_id).count()
            
            questions_data = [question.to_dict() for question in questions]
            
            return {
                'message': f'Successfully retrieved {len(questions_data)} questions',
                'campaign_id': campaign_id,
                'campaign_name': campaign.name,
                'pagination': {
                    'total_count': total_count,
                    'returned_count': len(questions_data),
                    'offset': offset,
                    'limit': limit
                },
                'questions': questions_data
            }, 200
            
        except Exception as e:
            logger.error(f"Error in advanced questions fetch for campaign {campaign_id}: {str(e)}", exc_info=True)
            return {'message': 'An internal error occurred while fetching questions'}, 500