"""
Defining the model for each table/model for an
api
"""
from . import db


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    api_id = db.Column(db.Integer, db.ForeignKey('api.id'))
    api = db.relationship('Api', back_populates='tables')
    table_parameters = db.relationship('TableParameter', back_populates='table', cascade="all, delete-orphan, delete")
    reference = db.relationship('ForeignKeyFieldReferenceTable', back_populates='table_reference', cascade='all, delete-orphan, delete', passive_deletes=True, uselist=False)
    entry_lists = db.relationship('EntryList', back_populates='table', cascade="all, delete-orphan, delete")
    reverse_relationships = db.relationship('relationship', backref='child_table', cascade="all, delete-orphan, delete")