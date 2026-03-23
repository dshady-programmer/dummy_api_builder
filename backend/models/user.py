"""
Defining the user model
"""
from . import db
from sqlalchemy import CheckConstraint

MAX_ROWS_FOR_CSV = 100
MAX_ROW_FOR_USER = 2000

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(64), unique=True, nullable=True)
    last_public_id_created = db.Column(db.DateTime, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    api_token = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), nullable=False)
    user_apis = db.relationship('Api', back_populates='user')
    user_limit_ref = db.relationship('UserLimit', back_populates='user_ref', uselist=False, cascade="all, delete-orphan, delete")
    

    def __str__(self):
        return f'User(id={self.id}, email={self.email}, public_id={self.public_id})'



class UserLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    user_ref = db.relationship('User', back_populates='user_limit_ref')
    current_rows = db.Column(db.Integer, nullable=False, default=0)
    max_rows = db.Column(db.Integer, nullable=False, default=MAX_ROW_FOR_USER)

    __table_args__ = (
        CheckConstraint('current_rows <= max_rows', name='check_current_rows_not_exceed_max_rows'),
    )

    def __str__(self):
        return f'UserLimit(id={self.id}, user_id={self.user_id}, current_rows={self.current_rows}, max_rows={self.max_rows})'