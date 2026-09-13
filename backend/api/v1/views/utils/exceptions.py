from functools import wraps
from sqlalchemy.exc import IntegrityError
from models import db

def exception_handler(func):
    """
    Decorator to handle exceptions in API endpoints.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:

            db.session.rollback()            
            return format_response(status="error", message="Database integrity error occurred", code=400)
        except Exception as e:
            
            return format_response(status="error", message="An unexpected error occurred", code=500)
        
    return wrapper