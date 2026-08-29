"""
Defining the model for each table/model for an
api
"""
from . import db

# name and api_id index

class Table(db.Model):
    """
        Table model to keep track of user created tables
        id: autoincrement, model primary key
        name: Name of the table
        description: Description of the table
        api_id: Foreign key to the Api model
        api: Relationship to the Api model for back reference (table.api gives the api the table belongs to)
        table_parameters: Relationship to the TableParameter model for back reference (table.table_parameters gives all parameters in the table)
                         table parameters are the fields in the table e.g a Car table would have parameters like make, model, year, color etc
        entry_lists: Relationship to the EntryList model for back reference (table.entry_lists gives all entry lists in the table)
                    entry lists are the rows in the table e.g a Car table would have entry lists like [make: 'Toyota', model: 'Camry', year: 2020, color: 'Blue'], [make: 'Honda', model: 'Civic', year: 2019, color: 'Red'] etc
        
        **reverse_relationships: Relationship to the Relationship model for back reference
                              Keeps track of   foreign key relationship.
                              e.g
                                Post table:


        reference: Relationship to the ForeignKeyFieldReferenceTable model for back reference (table.reference gives the foreign key reference for the table)
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    api_id = db.Column(db.Integer, db.ForeignKey('api.id', ondelete='CASCADE'), index=True)
    api = db.relationship('Api', back_populates='tables')
    table_parameters = db.relationship('TableParameter', back_populates='table', cascade="all, delete-orphan", passive_deletes=True)
    reference = db.relationship('ForeignKeyFieldReferenceTable', back_populates='table_reference', cascade='all, delete-orphan', uselist=False, passive_deletes=True)
    entry_lists = db.relationship('EntryList', back_populates='table', cascade="all, delete-orphan", passive_deletes=True)
    reverse_relationships = db.relationship('Relationship', backref='child_table', cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        db.UniqueConstraint('api_id', 'name', name='uq_table_api_id_table_name'),
        {'sqlite_autoincrement': True}  # Ensure that the id is always incremented and not reused after deletion
    )