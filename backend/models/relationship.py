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
    """
        Relationship model to define foreign key relationships between tables
        id: autoincrement, model primary key
        entry_ref_pk: Reference to the primary key column to the particular foreign key table entry
        entrylists: Many to Many Relationship to the EntryList model for back reference (relationship.entrylists gives all the reverse relationship entry lists that reference the foreign key table)
                   e.g 
                     User table;
                        name: string - tableparameter
                        email: string - tableparameter
    
                    
                     Post table:
                        title: string - tableparameter
                        content: string - tableparameter
                        user_id: foreign key - tableparameter
                    
                    Relationship:
                        entry_ref_pk = user_id = 2
                        entrylists:
                            User.get(id=user_id).posts (gets all the user's posts)
                            user.posts 

                        foreign_key_rel_id: User reference table
                        child_table_id: Post table

        foreign_key_rel_id: Foreign key to the ForeignKeyFieldReferenceTable model (the parent
        child_table_id: Foreign key to the child table (the table that has the foreign key)
    """
    id = db.Column(db.Integer, primary_key=True)
    entry_ref_pk = db.Column(db.String, nullable=False) # reference to foreign key primary key
    entrylists = db.relationship("EntryList", secondary=entrylist_relationships, backref="relationships")
    foreign_key_rel_id = db.Column(db.Integer, db.ForeignKey('foreignkeyfieldreferencetable.id', ondelete='CASCADE'))  # parent table reference for the foreign key relationship
    child_table_id = db.Column(db.Integer, db.ForeignKey('table.id', ondelete='CASCADE')) # child table reference for the foreign key relationship
