from functools import wraps
from sqlalchemy.exc import IntegrityError
from models import db
from .response import format_response
import traceback


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
            print('errored out')
            print(str(e))
            # raise e
            # print(traceback.print_exc())
            return format_response(status="error", message="An unexpected error occurred", code=500)
        
    return wrapper