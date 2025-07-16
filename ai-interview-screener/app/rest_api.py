from flask_restful import Api
from app.api.auth_routes import RegisterResource, LoginResource, LogoutResource
from app.api.campaign_routes import CampaignListResource, CampaignResource, CandidateUploadResource, StartCampaignResource, UploadedCSVListResource
from app.api.interview_routes import CallHandlerResource, RecordingHandlerResource, CampaignResultsResource

def register_routes(app):
    api = Api(app, prefix='/api')
    
    # Authentication routes
    api.add_resource(RegisterResource, '/auth/register')
    api.add_resource(LoginResource, '/auth/login')
    api.add_resource(LogoutResource, '/auth/logout')
    
    # Campaign routes
    api.add_resource(CampaignListResource, '/campaigns')
    api.add_resource(CampaignResource, '/campaigns/<int:campaign_id>')
    api.add_resource(CandidateUploadResource, '/campaigns/<int:campaign_id>/candidates')
    api.add_resource(StartCampaignResource, '/campaigns/<int:campaign_id>/start')
    api.add_resource(UploadedCSVListResource, '/csvs')
    # Interview routes
    api.add_resource(CallHandlerResource, '/voice/call_handler')
    api.add_resource(RecordingHandlerResource, '/voice/recording_handler')
    api.add_resource(CampaignResultsResource, '/campaigns/<int:campaign_id>/results')