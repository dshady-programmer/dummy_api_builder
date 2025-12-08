"""
Creating constraints table with a many to many
relationship to table_parameters
"""

from . import db
import enum


class ValidConstraints(enum.Enum):
    foreign_key = 'foreign_key'
    unique = 'unique'
    nullable = 'nullable'
    primary_key = 'primary_key'
    default = 'default'

class Constraint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum(ValidConstraints), default=ValidConstraints.nullable, nullable=False, unique=True)