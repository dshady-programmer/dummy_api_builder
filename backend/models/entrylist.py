"""
Defining the model for entry lists
think of entry list as the entire row and entry as each column in a row.
e.g
name: peter
age: 15
e.t.c..
"""
from . import db
        # table_id and primary_key_value as index


class EntryList(db.Model):
    """
        EntryList model to keep track of the entry lists for each table
        id: autoincrement, model primary key
        primary_key_value: The value of the primary key for the entry list (could be composite i.e combination of more than one table parameter)
        entries: Relationship to the Entry model for back reference (entry_list.entries gives all entries in the entry list)
                an entrylist is equivalent to a row in the table. e.g a Car table would have entry lists like 
                        entrylist 1 - [make: 'Toyota', model: 'Camry', year: 2020, color: 'Blue']
                        entrylist 2 - [make: 'Honda', model: 'Civic', year: 2019, color: 'Red'] etc

                        where 
                            - make: 'Toyota' is the entry for entrylist 1
                            - model: 'Camry' is the entry for entrylist 1
                            - year: 2020 is the entry for entrylist 1
                            - color: 'Blue' is the entry for entrylist 1
                        so entrylist.entries for entrylist would give
                             [
                                Entry 1 - make: 'Toyota'
                                Entry 2 - model: 'Camry'
                                Entry 3 - year: 2020
                                Entry 4 - color: 'Blue'
                            ]
        table_id: Foreign key to the Table model
        table: Relationship to the Table model for back reference (entry_list.table gives the table the entry list belongs to)
    """
    __tablename__ = 'entrylist'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    primary_key_value = db.Column(db.Text)
    entries = db.relationship('Entry', back_populates='entry_list', cascade="all, delete-orphan", passive_deletes=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id', ondelete='CASCADE')) 
    table = db.relationship('Table', back_populates='entry_lists')

    
    __table_args__ = (
        db.UniqueConstraint('table_id', 'primary_key_value', name='uq_entrylist_table_id_primary_key_value'),
        {'sqlite_autoincrement': True}  # Ensure that the id is always incremented and not reused after 
    )