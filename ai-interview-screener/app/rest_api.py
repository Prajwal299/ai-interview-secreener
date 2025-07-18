

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
from app.api.campaign_routes import CampaignListResource, CampaignResource, CandidateUploadResource, StartCampaignResource, UploadedCSVListResource
from app.api.interview_routes import CallHandlerResource, CandidateResultsResource, RecordingHandlerResource, CampaignResultsResource, CallStatusHandlerResource, RecordingStatusHandlerResource
import logging
from flask import request
from app.models import Candidate, Campaign
from app import db

logger = logging.getLogger(__name__)

def register_routes(app, socketio):  # Accept socketio as a parameter
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
    
    # Interview routes
    api.add_resource(CallHandlerResource, '/voice/call_handler')
    api.add_resource(RecordingHandlerResource, '/voice/recording_handler')
    api.add_resource(CampaignResultsResource, '/campaigns/<int:campaign_id>/results')
    api.add_resource(CallStatusHandlerResource, '/voice/status')
    api.add_resource(RecordingStatusHandlerResource, '/voice/recording_status')
    api.add_resource(CandidateResultsResource, '/candidates/<int:candidate_id>/results')

    # Define emit_campaign_update within register_routes to use socketio
    def emit_campaign_update(campaign_id):
        socketio.emit('campaign_update', {'campaign_id': campaign_id}, namespace='/campaigns')

    # Update CallStatusHandlerResource to use emit_campaign_update
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
                            emit_campaign_update(campaign.id)  # Emit WebSocket event
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

    # Register the updated CallStatusHandlerResource
    api.add_resource(CallStatusHandlerResource, '/voice/status')