from sqlalchemy import event
from models.table import Table


@event.listens_for(Table, 'before_delete')
def prevent_delete_if_locked(mapper, connection, target):
    if getattr(target, 'is_locked', False):
        raise ValueError(f"Can't delete {target.name}: A child table has its primary key reference it via a foreign key relationship")

