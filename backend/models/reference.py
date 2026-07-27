"""

To keep references to the foreign key table reference.

"""
from . import db

class ForeignKeyFieldReferenceTable(db.Model):
    """
        ForeignKeyFieldReferenceTable model to keep track of the foreign key references for each table
        id: autoincrement, model primary key
        table_id: Foreign key to the Table model
        table_reference: Relationship to the Table model for back reference (foreign_key_field_reference_table.table_reference gives the table the foreign key reference belongs to)
        table_parameter_references: Relationship to the TableParameter model for back reference (foreign_key_field_reference_table.table_parameter_references gives all table parameters that reference the foreign key table)
        relationship_references: Relationship to the Relationship model for back reference (foreign_key_field_reference_table.relationship_references gives all relationships that reference the foreign key table)
    """
    __tablename__ = 'foreignkeyfieldreferencetable'
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id', ondelete='CASCADE'), unique=True) # one to one relationship with table
    table_reference = db.relationship('Table', back_populates='reference')
    table_parameter_references = db.relationship('TableParameter', backref='foreign_key_reference_table', cascade='all, delete-orphan', passive_deletes=True) # Deleting the Parent table automatically deletes all the table parameters associated with it on all child tables
    relationship_references = db.relationship('Relationship', backref='foreign_key_rel', cascade='all, delete-orphan', passive_deletes=True)
