"""
Defining the model for each field in the database
e.g name: 'peter' type: 'string' nullable: false
etc. The model would be similar to the table parameter
"""
from . import db


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Text, nullable=True)
    tableparameter_id = db.Column(db.Integer, db.ForeignKey('tableparameter.id'))
    tableparameter = db.relationship('TableParameter', back_populates='entries')
    entry_list_id = db.Column(db.Integer, db.ForeignKey('entrylist.id'))
    entry_list = db.relationship('EntryList', back_populates='entries')
