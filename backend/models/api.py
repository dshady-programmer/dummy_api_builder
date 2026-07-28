"""
Defining the model for a user created api
"""

from . import db


class Api(db.Model):

    """
        Api model to keep track of user created apis
        id: autoincrement, model primary key
        name: Name of the api
        description: Description of the api
        user_id: Foreign key to the User model
        user: Relationship to the User model for back reference
        tables: Relationship to the Table model for back reference(api.tables gives all tables in the api)
        is_locked: Determines whether an api is allowed to be deleted or not
            This happens when the api is referenced by another table usually as a foreign key 
            and that foreign key field is a primary key on that table.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User', back_populates='user_apis')
    tables = db.relationship('Table', back_populates='api', cascade='all, delete-orphan, delete')
