# from flask_restful import Api
# from app.api.auth_routes import RegisterResource, LoginResource, LogoutResource
# from app.api.campaign_routes import CampaignListResource, CampaignResource, CandidateUploadResource, StartCampaignResource, UploadedCSVListResource
# from app.api.interview_routes import CallHandlerResource, CallStatusHandlerResource, RecordingHandlerResource, CampaignResultsResource, SimpleTestHandler

# def register_routes(app):
#     api = Api(app, prefix='/api')
    
#     # Authentication routes
#     api.add_resource(RegisterResource, '/auth/register')
#     api.add_resource(LoginResource, '/auth/login')
#     api.add_resource(LogoutResource, '/auth/logout')
    
#     # Campaign routes
#     api.add_resource(CampaignListResource, '/campaigns')
#     api.add_resource(CampaignResource, '/campaigns/<int:campaign_id>')
#     api.add_resource(CandidateUploadResource, '/campaigns/<int:campaign_id>/candidates')
#     api.add_resource(StartCampaignResource, '/campaigns/<int:campaign_id>/start')
#     api.add_resource(UploadedCSVListResource, '/csvs')
#     # Interview routes
#     api.add_resource(CallHandlerResource, '/voice/call_handler')
#     api.add_resource(RecordingHandlerResource, '/voice/recording_handler')
#     api.add_resource(CampaignResultsResource, '/campaigns/<int:campaign_id>/results')

#     api.add_resource(CallStatusHandlerResource, '/voice/status')

#     api.add_resource(SimpleTestHandler, '/voice/simple_test')



# app/rest_api.py

# from flask_restful import Api
# from app.api.auth_routes import RegisterResource, LoginResource, LogoutResource
# from app.api.campaign_routes import CampaignListResource, CampaignResource, CandidateUploadResource, StartCampaignResource, UploadedCSVListResource

# # ✅ FIX: Removed 'SimpleTestHandler' from this import
# from app.api.interview_routes import (
#     CallHandlerResource, 
#     CallStatusHandlerResource, 
#     RecordingHandlerResource, 
#     CampaignResultsResource,
#     RecordingStatusHandlerResource
# )

# def register_routes(app):
#     api = Api(app, prefix='/api')
    
#     # --- Authentication routes ---
#     api.add_resource(RegisterResource, '/auth/register')
#     api.add_resource(LoginResource, '/auth/login')
#     api.add_resource(LogoutResource, '/auth/logout')
    
#     # --- Campaign routes ---
#     api.add_resource(CampaignListResource, '/campaigns')
#     api.add_resource(CampaignResource, '/campaigns/<int:campaign_id>')
#     api.add_resource(CandidateUploadResource, '/campaigns/<int:campaign_id>/candidates')
#     api.add_resource(StartCampaignResource, '/campaigns/<int:campaign_id>/start')
#     api.add_resource(UploadedCSVListResource, '/csvs')

#     # --- Interview routes ---
#     api.add_resource(CallHandlerResource, '/voice/call_handler')
#     api.add_resource(RecordingHandlerResource, '/voice/recording_handler')
#     api.add_resource(CampaignResultsResource, '/campaigns/<int:campaign_id>/results')
#     api.add_resource(CallStatusHandlerResource, '/voice/status')

#     api.add_resource(RecordingStatusHandlerResource, '/voice/recording_status')



from flask_restful import Api
from app.api.auth_routes import AuthLoginResource, AuthRegisterResource, AuthLogoutResource
from app.api.campaign_routes import CampaignResource, CampaignsResource, CampaignCandidatesResource, CampaignStartResource
from app.api.csv_routes import CSVsResource
from app.api.interview_routes import CallHandlerResource, RecordingHandlerResource, CampaignResultsResource

def register_routes(app):
    api = Api(app)
    
    # Authentication routes
    api.add_resource(AuthLoginResource, '/api/auth/login')
    api.add_resource(AuthRegisterResource, '/api/auth/register')
    api.add_resource(AuthLogoutResource, '/api/auth/logout')
    
    # Campaign routes
    api.add_resource(CampaignsResource, '/api/campaigns')
    api.add_resource(CampaignResource, '/api/campaigns/<int:campaign_id>')
    api.add_resource(CampaignCandidatesResource, '/api/campaigns/<int:campaign_id>/candidates')
    api.add_resource(CampaignStartResource, '/api/campaigns/<int:campaign_id>/start')
    
    # CSV routes
    api.add_resource(CSVsResource, '/api/csvs')
    
    # Interview routes
    api.add_resource(CallHandlerResource, '/api/voice/call_handler')
    api.add_resource(RecordingHandlerResource, '/api/voice/recording_handler')
    api.add_resource(CampaignResultsResource, '/api/campaigns/<int:campaign_id>/results')