# from flask_restful import Resource, reqparse
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from flask import request
# from app.models import Campaign, Candidate, InterviewQuestion, User
# from app.services.ai_service import AIService
# from app.services.twilio_service import TwilioService
# from app import db
# import csv
# import io

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
        
#         # Create campaign
#         campaign = Campaign(
#             name=args['name'],
#             job_description=args['job_description'],
#             user_id=user_id
#         )
        
#         db.session.add(campaign)
#         db.session.commit()
        
#         # Generate AI questions
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
#             return {'message': 'Campaign not found'}, 404
        
#         if 'file' not in request.files:
#             return {'message': 'No file provided'}, 400
        
#         file = request.files['file']
#         if file.filename == '':
#             return {'message': 'No file selected'}, 400
        
#         if not file.filename.endswith('.csv'):
#             return {'message': 'File must be a CSV'}, 400
        
#         # Process CSV file
#         stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
#         csv_reader = csv.DictReader(stream)
        
#         candidates_added = 0
#         for row in csv_reader:
#             if 'name' in row and 'phone_number' in row:
#                 candidate = Candidate(
#                     name=row['name'],
#                     phone_number=row['phone_number'],
#                     email=row.get('email', ''),
#                     campaign_id=campaign_id
#                 )
#                 db.session.add(candidate)
#                 candidates_added += 1
        
#         db.session.commit()
        
#         return {'message': f'{candidates_added} candidates added successfully'}, 201

# class StartCampaignResource(Resource):
#     @jwt_required()
#     def post(self, campaign_id):
#         user_id = get_jwt_identity()
#         campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
#         if not campaign:
#             return {'message': 'Campaign not found'}, 404
        
#         if campaign.status != 'created':
#             return {'message': 'Campaign is not in created status'}, 400
        
#         # Update campaign status
#         campaign.status = 'running'
#         db.session.commit()
        
#         # Start calling candidates
#         twilio_service = TwilioService()
#         results = twilio_service.start_campaign_calls(campaign)
        
#         return {'message': 'Campaign started successfully', 'call_results': results}, 200

from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from app.models import Campaign, Candidate, InterviewQuestion, User, UploadedCSV
from app.services.ai_service import AIService
from app.services.twilio_service import TwilioService
from app import db
import csv
import io
import os

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
            return {'message': 'Campaign not found'}, 404
        
        if 'file' not in request.files:
            return {'message': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'message': 'No file selected'}, 400
        
        if not file.filename.endswith('.csv'):
            return {'message': 'File must be a CSV'}, 400
        
        # Store CSV in database
        csv_content = file.read()
        uploaded_csv = UploadedCSV(
            filename=file.filename,
            content=csv_content,
            user_id=user_id
        )
        db.session.add(uploaded_csv)
        db.session.commit()
        
        # Process CSV file
        stream = io.StringIO(csv_content.decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        candidates_added = 0
        for row in csv_reader:
            if 'name' in row and 'phone_number' in row:
                candidate = Candidate(
                    name=row['name'],
                    phone_number=row['phone_number'],
                    email=row.get('email', ''),
                    campaign_id=campaign_id
                )
                db.session.add(candidate)
                candidates_added += 1
        
        db.session.commit()
        
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
            return {'message': 'Campaign not found'}, 404
        
        if campaign.status != 'created':
            return {'message': 'Campaign is not in created status'}, 400
        
        campaign.status = 'running'
        db.session.commit()
        
        twilio_service = TwilioService()
        results = twilio_service.start_campaign_calls(campaign)
        
        return {'message': 'Campaign started successfully', 'call_results': results}, 200

class UploadedCSVListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        csvs = UploadedCSV.query.filter_by(user_id=user_id).all()
        return {'csvs': [csv.to_dict() for csv in csvs]}, 200