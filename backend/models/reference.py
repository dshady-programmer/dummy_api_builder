"""

To keep references to the foreign key table reference.

"""
from . import db

class ForeignKeyFieldReferenceTable(db.Model):
    __tablename__ = 'foreignkeyfieldreferenceTable'
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), unique=True) # one to one relationship with table
    table_reference = db.relationship('Table', back_populates='reference')
    table_parameter_references = db.relationship('TableParameter', backref='foreign_key_reference_table', cascade='all, delete-orphan, delete', passive_deletes=True)
    relationship_references = db.relationship('Relationship', backref='foreign_key_rel', cascade='all, delete-orphan, delete', passive_deletes=True)
