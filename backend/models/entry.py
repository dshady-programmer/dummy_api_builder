"""
Defining the model for each field in the database
e.g name: 'peter' type: 'string' nullable: false
etc. The model would be similar to the table parameter
"""
from . import db


class Entry(db.Model):
    """
        Entry table to keep track of the entries for each table parameter (table columns)
             e.g name: 'peter' type: 'string' nullable: false
                 age: 25 type: 'integer' nullable: false
        id: autoincrement, model primary key
        value: The value of the entry for the table parameter
        tableparameter_id: Foreign key to the TableParameter model 
        tableparameter: Relationship to the TableParameter model for back reference (entry.tableparameter gives the table parameter the entry belongs to)
        entry_list_id: Foreign key to the EntryList model
        entry_list: Relationship to the EntryList model for back reference (entry.entry_list gives the entry list the entry belongs to)
                    an entry list is a row in the table. e.g a Car table would have entry lists like 
                        entrylist 1 - [make: 'Toyota', model: 'Camry', year: 2020, color: 'Blue']
                        entrylist 2 - [make: 'Honda', model: 'Civic', year: 2019, color: 'Red'] etc

                        where 
                            - make: 'Toyota' is the entry for entrylist 1
                            - model: 'Camry' is the entry for entrylist 1
                            - year: 2020 is the entry for entrylist 1
                            - color: 'Blue' is the entry for entrylist 1
        

    """
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Text, nullable=True)
    tableparameter_id = db.Column(db.Integer, db.ForeignKey('tableparameter.id', ondelete='CASCADE'))
    tableparameter = db.relationship('TableParameter', back_populates='entries')
    entry_list_id = db.Column(db.Integer, db.ForeignKey('entrylist.id', ondelete='CASCADE'))
    entry_list = db.relationship('EntryList', back_populates='entries')
