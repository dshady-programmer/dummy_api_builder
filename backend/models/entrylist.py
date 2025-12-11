"""
Defining the model for entry lists
think of entry list as the entire row and entry as each column in a row.
e.g
name: peter
age: 15
e.t.c..
"""
from . import db


class EntryList(db.Model):
    __tablename__ = 'entrylist'
    id = db.Column(db.Integer, primary_key=True)
    primary_key_value = db.Column(db.Text)
    entries = db.relationship('Entry', back_populates='entry_list', cascade="all, delete-orphan, delete")
    table_id = db.Column(db.Integer, db.ForeignKey('table.id')) 
    table = db.relationship('Table', back_populates='entry_lists')
    