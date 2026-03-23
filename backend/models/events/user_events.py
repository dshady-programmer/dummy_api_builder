from models.user import User, UserLimit
from sqlalchemy import event


@event.listens_for(User, "after_insert")
def create_reference_table(mapper, connection, target):

    connection.execute(
        UserLimit.__table__.insert().values(
            user_id=target.id
        )
    )