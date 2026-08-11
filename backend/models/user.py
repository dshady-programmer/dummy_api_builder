"""
Defining the user model
"""
from . import db
from sqlalchemy import CheckConstraint

MAX_ROWS_FOR_CSV = 100
MAX_ROW_FOR_USER = 2000


# api token (index)

class User(db.Model):

    """
        User model to keep track of user entries

        id: autoincrement, model primary key
        public_id: For authentication purpose.
        last_public_id_created: Last time public_id was created 
        email: User email
        api_token: User personal api token for access their api space
        password: User password
        user_apis: all apis linked to the user
        user_limit_ref: Foreign key to the UserLimit model to keep track of the number of rows a user has created

    """
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(64), unique=True, nullable=True)
    last_public_id_created = db.Column(db.DateTime, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    api_token = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), nullable=False)
    user_apis = db.relationship('Api', back_populates='user', cascade="all, delete-orphan", passive_deletes=True)
    user_limit_ref = db.relationship('UserLimit', back_populates='user_ref', uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    

    def __str__(self):
        return f'User(id={self.id}, email={self.email}, public_id={self.public_id})'



class UserLimit(db.Model):
    """
        UserLimit model to keep track of the number of rows a user has created

        id: autoincrement, model primary key
        user_id: Foreign key to the User model
        user_ref: Relationship to the User model for back reference
        current_rows: Number of rows the user has created
        max_rows: Maximum number of rows the user can create
        check_constraint: Ensure current_rows does not exceed max_rows
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True, nullable=False)
    user_ref = db.relationship('User', back_populates='user_limit_ref')
    current_rows = db.Column(db.Integer, nullable=False, default=0)
    max_rows = db.Column(db.Integer, nullable=False, default=MAX_ROW_FOR_USER)

    __table_args__ = (
        CheckConstraint('current_rows <= max_rows', name='check_current_rows_not_exceed_max_rows'),
    )

    def __str__(self):
        return f'UserLimit(id={self.id}, user_id={self.user_id}, current_rows={self.current_rows}, max_rows={self.max_rows})'