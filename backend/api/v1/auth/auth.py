"""
Contains jwt authentication decorator
that checks if the token is set and the user's
session is valid.
"""
from functools import wraps
from flask import request, jsonify
import jwt


def login_required(f):
    """
    Gets and verifies the token from the
    request
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from api.v1.app import app
        from models.user import User
        from models import db
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'],algorithms=["HS256"])

            stmt = db.select(User).filter_by(public_id=data['public_id'])
            current_user = db.session.scalars(stmt).first()
        except Exception as e:
            print('exception', e)
            return jsonify({
                'error' : 'Token is invalid !!'
            }), 401
        if not current_user:
            return jsonify({
                'error': 'invalid credentials, please log in or create an account'
            }), 401
        # returns the current logged in users context to the routes
        return  f(current_user, *args, **kwargs)
    return decorated

