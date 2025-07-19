AI Interview Screener - Backend
Overview
This is the backend for the AI Interview Screener, a Flask-based application that automates phone-based candidate screening using Twilio for voice calls and Grok for generating interview questions. It handles campaign creation, candidate management, question generation, and call flow orchestration.
Tech Stack

Language: Python 3.8+
Framework: Flask
Database: PostgreSQL (AWS RDS)
Voice Integration: Twilio
AI: Grok (via xAI API)
Dependencies: Managed via requirements.txt

Prerequisites

Python 3.8 or higher
PostgreSQL database (e.g., AWS RDS)
Twilio account with a phone number
xAI API key for Grok
Redis (optional, for caching or queue management)
Git

Setup Instructions

Clone the Repository:
git clone <repository-url>
cd ai-interview-screener/ai-interview-screener


Set Up Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Configure Environment Variables:Create a .env file in the root directory:
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:<password>@ai-interview-db-instance.c5e0c0k4gq9h.ap-south-1.rds.amazonaws.com:5432/ai_interview_db
TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
TWILIO_PHONE_NUMBER=<your-twilio-phone-number>
XAI_API_KEY=<your-xai-api-key>


Initialize the Database:Ensure your PostgreSQL database is running, then apply migrations:
flask db init
flask db migrate
flask db upgrade


Run the Application:
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app

The backend will be available at http://<your-server-ip>:5000.


Key Endpoints

GET/POST /api/voice/call_handler: Generates TwiML for Twilio call flow (greeting, questions, recording).
POST /api/voice/status: Handles Twilio call status callbacks (e.g., updates candidate status).
GET /api/campaigns: Retrieves all campaigns for a user.
POST /api/campaigns: Creates a new campaign with candidate CSV upload.
POST /api/campaigns/<id>/start: Starts a campaign, initiating calls.

Directory Structure
ai-interview-screener/
├── app/
│   ├── api/
│   │   └── interview_routes.py  # Call handling and campaign endpoints
│   ├── models/                 # SQLAlchemy models (Candidate, Campaign, InterviewQuestion)
│   ├── services/
│   │   ├── ai_service.py       # Grok integration for question generation
│   │   └── twilio_service.py   # Twilio call initiation and management
│   ├── __init__.py             # Flask app setup
│   └── wsgi.py                 # Gunicorn entry point
├── instance/
│   └── app.log                 # Application logs
├── requirements.txt
└── .env

Testing

Unit Tests:pytest tests/


Manual Testing:
Create a campaign via the frontend or POST to /api/campaigns.
Start a campaign and monitor logs:tail -f instance/app.log


Verify Twilio calls and database updates (e.g., candidates.call_status).



Debugging

Check logs: tail -f instance/app.log
Verify Twilio webhook: http://<your-server-ip>:5000/api/voice/call_handler?candidate_id=<id>
Query database:psql -h ai-interview-db-instance.c5e0c0k4gq9h.ap-south-1.rds.amazonaws.com -U postgres -d ai_interview_db
SELECT * FROM campaigns;



Deployment

Deploy on an AWS EC2 instance or similar.
Use Nginx as a reverse proxy.
Ensure port 5000 is open:sudo ufw allow 5000



Contributing

Fork the repository.
Create a feature branch: git checkout -b feature-name
Submit a pull request with clear descriptions.

License
MIT License
