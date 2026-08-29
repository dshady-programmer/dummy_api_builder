"""
Creating constraints table with a many to many
relationship to table_parameters
"""

from . import db
import enum


class ValidConstraints(enum.Enum):
    """
        Enum for the valid constraints that can be applied to a table parameter
    """
    foreign_key = 'foreign_key'
    unique = 'unique'
    nullable = 'nullable'
    primary_key = 'primary_key'
    default = 'default'

class Constraint(db.Model):
    """
        Constraint model to keep track of the constraints applied to a table parameter
        id: autoincrement, model primary key
        name: Name of the constraint (can either be foreign_key, unique, nullable, primary_key, default)
             nullable and default are mutually exclusive. A table parameter can either be nullable or have a default value, but not both.
             nullable and unique are mutually inclusive. A table parameter is allowed be nullable and unique,
                    but would mean whenever you add a value it must be unique.
            
            for unique and default. 
                A table parameter can either be unique or have a default value, but not both.
                        exception is primary key as the default value is generated automatically for primary keys 
                            and uniqueness would be guaranteed
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Enum(ValidConstraints), default=ValidConstraints.nullable, nullable=False, unique=True)

    __table_args__ = {'sqlite_autoincrement': True}  # Ensure that the id is always incremented and not reused after deletion