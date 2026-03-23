"""
Defining the user model
"""
from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(64), unique=True, nullable=True)
    last_public_id_created = db.Column(db.DateTime, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    api_token = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), nullable=False)
    user_apis = db.relationship('Api', back_populates='user')
    user_limit = db.relationship('UserLimit', back_populates='user', uselist=False, cascade="all, delete-orphan, delete")
    

    def __str__(self):
        return f'User(id={self.id}, email={self.email}, public_id={self.public_id})'



class UserLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='user_limit')
    current_rows = db.Column(db.Integer, nullable=False, default=0)
    max_rows = db.Column(db.Integer, nullable=False, default=1000)

    def __str__(self):
        return f'UserLimit(id={self.id}, user_id={self.user_id}, current_rows={self.current_rows}, max_rows={self.max_rows})'