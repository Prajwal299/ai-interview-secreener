from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt
from flask import jsonify

def check_blacklist(f):
    """Decorator to check if JWT token is blacklisted"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        jti = get_jwt()['jti']
        from app.api.auth_routes import blacklisted_tokens
        
        if jti in blacklisted_tokens:
            return jsonify({'message': 'Token has been revoked'}), 401
        
        return f(*args, **kwargs)
    return decorated_function