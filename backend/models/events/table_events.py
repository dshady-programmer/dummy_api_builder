from models.table import Table
from sqlalchemy.orm import Session
from models.reference import ForeignKeyFieldReferenceTable
from sqlalchemy import event


@event.listens_for(Table, "after_insert")
def create_reference_table(mapper, connection, target):

    # Get the session that is inserting the Table
    session = Session.object_session(target)
    fk = ForeignKeyFieldReferenceTable(table_id=target.id)
    session.add(fk)