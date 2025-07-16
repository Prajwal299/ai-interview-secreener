from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.models import User
from app import db

# In-memory blacklist for JWT tokens (use Redis in production)
blacklisted_tokens = set()

class RegisterResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required')
        parser.add_argument('email', type=str, required=True, help='Email is required')
        parser.add_argument('password', type=str, required=True, help='Password is required')
        args = parser.parse_args()
        
        # Check if user already exists
        if User.query.filter_by(username=args['username']).first():
            return {'message': 'Username already exists'}, 400
        
        if User.query.filter_by(email=args['email']).first():
            return {'message': 'Email already exists'}, 400
        
        # Create new user
        user = User(username=args['username'], email=args['email'])
        user.set_password(args['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return {'message': 'User created successfully', 'user': user.to_dict()}, 201

class LoginResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required')
        parser.add_argument('password', type=str, required=True, help='Password is required')
        args = parser.parse_args()
        
        user = User.query.filter_by(username=args['username']).first()
        
        if user and user.check_password(args['password']):
            access_token = create_access_token(identity=str(user.id))
            return {
                'access_token': access_token,
                'user': user.to_dict()
            }, 200
        
        return {'message': 'Invalid credentials'}, 401

class LogoutResource(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        return {'message': 'Successfully logged out'}, 200