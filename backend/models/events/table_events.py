from models.table import Table
# from sqlalchemy.orm import Session
from models.reference import ForeignKeyFieldReferenceTable
from sqlalchemy import event


@event.listens_for(Table, "after_insert")
def create_reference_table(mapper, connection, target):

    connection.execute(
        ForeignKeyFieldReferenceTable.__table__.insert().values(
            table_id=target.id
        )
    )