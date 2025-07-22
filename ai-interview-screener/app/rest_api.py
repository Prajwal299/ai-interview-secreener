

# from flask_restful import Api
# from app.api.auth_routes import LoginResource, RegisterResource, LogoutResource
# from app.api.campaign_routes import CampaignListResource, CampaignResource, CandidateUploadResource, StartCampaignResource, UploadedCSVListResource
# from app.api.interview_routes import CallHandlerResource, RecordingHandlerResource, CampaignResultsResource, CallStatusHandlerResource, RecordingStatusHandlerResource

# def register_routes(app):
#     api = Api(app, prefix='/api')
    
#     # Authentication routes
#     api.add_resource(LoginResource, '/auth/login')
#     api.add_resource(RegisterResource, '/auth/register')
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
#     api.add_resource(RecordingStatusHandlerResource, '/voice/recording_status')



# from flask_restful import Api
# from app.api.auth_routes import LoginResource, RegisterResource, LogoutResource
# from app.api.campaign_routes import CampaignListResource, CampaignResource, CandidateUploadResource, StartCampaignResource, UploadedCSVListResource
# from app.api.interview_routes import CallHandlerResource, CandidateResultsResource, RecordingHandlerResource, CampaignResultsResource, CallStatusHandlerResource, RecordingStatusHandlerResource
# from flask_socketio import SocketIO

# socketio = SocketIO(app)


# def register_routes(app):
#     api = Api(app, prefix='/api')
    
#     # Authentication routes
#     api.add_resource(LoginResource, '/auth/login')
#     api.add_resource(RegisterResource, '/auth/register')
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
#     api.add_resource(RecordingStatusHandlerResource, '/voice/recording_status')
#     api.add_resource(CandidateResultsResource, '/candidates/<int:candidate_id>/results')

# # Emit status update
# def emit_campaign_update(campaign_id):
#     socketio.emit('campaign_update', {'campaign_id': campaign_id}, namespace='/campaigns')

from flask_restful import Api
from app.api.auth_routes import LoginResource, RegisterResource, LogoutResource
from app.api.campaign_routes import CampaignListResource, CampaignQuestionsAdvancedResource, CampaignQuestionsResource, CampaignResource, CandidateUploadResource, StartCampaignResource, UploadedCSVListResource
from app.api.interview_routes import CallHandlerResource, CandidateResultsResource, RecordingHandlerResource, CampaignResultsResource, CallStatusHandlerResource, RecordingStatusHandlerResource
import logging

logger = logging.getLogger(__name__)

def register_routes(app):  # Remove socketio parameter
    api = Api(app, prefix='/api')
    
    # Authentication routes
    api.add_resource(LoginResource, '/auth/login')
    api.add_resource(RegisterResource, '/auth/register')
    api.add_resource(LogoutResource, '/auth/logout')
    
    # Campaign routes
    api.add_resource(CampaignListResource, '/campaigns')
    api.add_resource(CampaignResource, '/campaigns/<int:campaign_id>')
    api.add_resource(CandidateUploadResource, '/campaigns/<int:campaign_id>/candidates')
    api.add_resource(StartCampaignResource, '/campaigns/<int:campaign_id>/start')
    api.add_resource(UploadedCSVListResource, '/csvs')
    
    api.add_resource(CampaignQuestionsResource, '/campaigns/<int:campaign_id>/questions')
    api.add_resource(CampaignQuestionsAdvancedResource, '/campaigns/<int:campaign_id>/questions/advanced')
    

    # Interview routes
    api.add_resource(CallHandlerResource, '/voice/call_handler')
    api.add_resource(RecordingHandlerResource, '/voice/recording_handler')
    api.add_resource(CampaignResultsResource, '/campaigns/<int:campaign_id>/results')
    api.add_resource(CallStatusHandlerResource, '/voice/status')
    api.add_resource(RecordingStatusHandlerResource, '/voice/recording_status')
    api.add_resource(CandidateResultsResource, '/candidates/<int:candidate_id>/results')

    logger.info("API routes registered")