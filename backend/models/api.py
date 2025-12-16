"""
Defining the model for a user created api
"""

from . import db


class Api(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='user_apis')
    tables = db.relationship('Table', back_populates='api', cascade='all, delete')