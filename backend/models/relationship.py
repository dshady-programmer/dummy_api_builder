"""
Relationship model to define ForeignKey
relationship
"""
from . import db


entrylist_relationships = db.Table('entrylist_relationships',
                                 db.Column('relationship_id', db.Integer, db.ForeignKey('relationship.id', name='fk_entrylist_relationships_relationship_id', ondelete='CASCADE')),
                                 db.Column('entrylist_id', db.Integer, db.ForeignKey('entrylist.id', name='fk_entrylist_relationships_entrylist_id', ondelete='CASCADE')),
                                 db.UniqueConstraint('relationship_id', 'entrylist_id', name='uq_relationship_entrylist')
                                 )


"""
Relationship allows reverse foreign key relationships...
"""

class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_ref_pk = db.Column(db.String, nullable=False) # reference to foreign key primary key
    entrylists = db.relationship("EntryList", secondary=entrylist_relationships, backref="relationships", passive_deletes=True)
    foreign_key_rel_id = db.Column(db.Integer, db.ForeignKey('foreignkeyreferencetable.id'))  # parent table reference for the foreign key relationship
    child_table_id = db.Column(db.Integer, db.ForeignKey('table')) # child table reference for the foreign key relationship
