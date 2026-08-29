"""
Defining the model for a user created api
"""

from . import db

# composite index of api_name and user_id

class Api(db.Model):

    """
        Api model to keep track of user created apis
        id: autoincrement, model primary key
        name: Name of the api
        description: Description of the api
        user_id: Foreign key to the User model
        user: Relationship to the User model for back reference
        tables: Relationship to the Table model for back reference(api.tables gives all tables in the api)

    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), index=True)
    user = db.relationship('User', back_populates='user_apis')
    tables = db.relationship('Table', back_populates='api', cascade='all, delete-orphan', passive_deletes=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_api_name_user_id'),
        db.Index("idx_api_id_user_id", "id", "user_id"),
        {'sqlite_autoincrement': True}  # Ensure that the id is always incremented and not reused after deletion
    )