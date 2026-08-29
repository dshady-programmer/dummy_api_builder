
from models import TableParameter, Relationship, Entry, EntryList,Table, entrylist_relationships
from sqlalchemy.orm import selectinload, joinedload
"""
    Utility functions for handling foreign key on delete operations in the API.
"""


"""
    table_level:
        protect: Can't delete the table i.e protect the child table foreign key field from being deleted
        cascade: Deletes the table parameter from the child table without deleting the entries
                    E.g Before delete:
                                child_table: post1: {"id": 1, "user_id": 3, "content": "Hello world"}
                        After delete:
                                child_table: post1: {"id": 1, "content": "Hello world"}

                    
                  The child table acts like it never referenced the parent table after the parent table is deleted
                    Use when child table is not strongly dependent on the parent table.
        
"""



def traverse_table_reference_child_tables(child_table_params, table_ids = None):


    if not child_table_params:
        return True # can delete.
    
    print('got here', child_table_params, table_ids)

    for c_table_param in child_table_params:
        # check each child table param for their on_delete config table param 

        table_on_delete = c_table_param.table_level_on_delete.name
        if not table_ids and table_on_delete == "protect":
            return False # protect child table from being deleted
        elif table_ids and c_table_param.table_id in table_ids:
            # There's no need to prevent tables under the same api from being deleted.
            continue
        elif table_on_delete == "cascade" and not c_table_param.primary_key:
            continue
        else:
            if c_table_param.primary_key:
                c_table_param.table_level_on_delete = "protect" # if by chance table level on_delete is "cascade" and the column is a primary key (if somehow the initial application code was bypassed)                
            return False 
        
    return True



def traverse_table_ref_entrylist_child_tables(db, fk_ref_table_id, pks, child_table_params, recursive_depth=1):

    print("recursive depth", recursive_depth)
    if recursive_depth > 5:
        raise RecursionError(
            "This schema exceeds the maximum relationship chain depth of 5 tables. Simplify your table or restructure your schema to reduce nesting."
            )
    recursive_depth += 1

    protected_child_table_ids = []
    nullable_child_table_ids = []
    nullable_child_table_param_ids = []
    cascade_child_table_ids = []
    for c_table_param in child_table_params:
        row_level_on_delete = c_table_param.row_level_on_delete.name
        if row_level_on_delete == "protect":
            protected_child_table_ids.append(c_table_param.table_id)
        elif row_level_on_delete == "set_null":
            nullable_child_table_ids.append(c_table_param.table_id)
            nullable_child_table_param_ids.append(c_table_param.id)
        else:
            cascade_child_table_ids.append(c_table_param.table_id)

    print('protected_child_table_ids', protected_child_table_ids)
    print('nullable_child_table_ids', nullable_child_table_ids)
    print('cascadde child_table_ids', cascade_child_table_ids)

    # first check if the protected child tables have existing rows that references the parent row to be deleted

    protected_rel_stmt = db.select(Relationship.entrylists.any()).where(
                                                                Relationship.entry_ref_pk.in_(pks), 
                                                                Relationship.foreign_key_rel_id==fk_ref_table_id,
                                                                Relationship.child_table_id.in_(protected_child_table_ids)
                                                            )
    
    
    is_ref = db.session.scalar(protected_rel_stmt)
    print('is ref', is_ref)
    if is_ref:
        return False # There's an active relationship on a protected row

    # If there isn't then check for others

    # handle cascade-able child tables
    # recursive call.
    
    if cascade_child_table_ids:
        # grab all the entrylist of that's referencing the pk
        cascade_rels_stmt = db.select(Relationship).where(
                                        Relationship.entry_ref_pk.in_(pks),
                                        Relationship.foreign_key_rel_id==fk_ref_table_id,
                                        Relationship.child_table_id.in_(cascade_child_table_ids)
                                    ).options(selectinload(Relationship.entrylists), joinedload(Relationship.child_table).joinedload(Table.reference))
        cascade_relationships = db.session.scalars(cascade_rels_stmt).all()


        # for each relationship bound by an on-delete cascade
        #   Get the child table reference table, the primary key of the rows affect and check recursively for the same constraints on grandchildren table
        #       Because other rows might depend on that child row.

        all_child_entrylists = [] # keep track so we can cascade them if all goes well.
        child_table_reference_entrylists = {}

        c_rel_ids = []
        for c_rel in cascade_relationships:
            c_rel_ids.append(c_rel.id)
            all_child_entrylists.extend(c_rel.entrylists)
            child_ref_t_id = c_rel.child_table.reference.id
            if child_ref_t_id in child_table_reference_entrylists:
                child_table_reference_entrylists[child_ref_t_id].union([e_list.primary_key_value for e_list in c_rel.entrylists]) # duplicates aren't expected anyway since each primary key is unique per table.
            else:
                child_table_reference_entrylists[child_ref_t_id] = set([e_list.primary_key_value for e_list in c_rel.entrylists])

        for child_ref_table_id, pks in child_table_reference_entrylists.items():
            stmt = db.select(TableParameter).where(TableParameter.foreign_key_reference_id == child_ref_table_id)
            grand_children_table_params = db.session.scalars(stmt).all()
            if not grand_children_table_params:
                continue
            can_delete = traverse_table_ref_entrylist_child_tables(db, child_ref_table_id, list(pks), grand_children_table_params, recursive_depth)

            if not can_delete:
                return False

        # if all ran recursively and no error with can_delete all True, then delete cascade_relationships.
        #   and delete individual entrylist associated with it 
        all_child_entrylist_ids = [e_list.id for e_list in all_child_entrylists]
        db.session.execute(
            db.delete(Relationship).where(Relationship.id.in_(c_rel_ids))
        )
        db.session.execute(
            db.delete(EntryList).where(EntryList.id.in_(all_child_entrylist_ids))
        )      


    # handle nullable child tables
    if nullable_child_table_ids:
        # set the entries of the nullable child table to null
        rel_stmt_subq = db.select(EntryList.id).join(Relationship.entrylists).where(
                                                                        Relationship.entry_ref_pk.in_(pks),
                                                                        Relationship.foreign_key_rel_id==fk_ref_table_id,
                                                                        Relationship.child_table_id.in_(nullable_child_table_ids)
                                                                        )

        update_entry_stmt = db.update(Entry).where(
                                                    Entry.entry_list_id.in_(rel_stmt_subq),
                                                    Entry.tableparameter_id.in_(nullable_child_table_param_ids)
                                                ).values(value=None)

        # dissociate the entrylist from the pk relationship
        delete_rel_stmt = db.delete(Relationship).where(
                                Relationship.entry_ref_pk.in_(pks),
                                Relationship.foreign_key_rel_id==fk_ref_table_id,
                                Relationship.child_table_id.in_(nullable_child_table_ids)
                            )

        # send to the db but don't execute yet.
        db.execute(update_entry_stmt)
        db.execute(delete_rel_stmt)
    return True
    
    


        



def delete_table(db, table):
    """
        Deletes table
    """
    reference = table.reference

    stmt = db.select(TableParameter).filter_by(foreign_key_reference_id=reference.id)
    child_table_params = db.session.scalars(stmt).all()
    print("child_table_params", child_table_params)
    try:
        can_delete = traverse_table_reference_child_tables(child_table_params)
        print("can delete", can_delete)

        if can_delete:
            try:
                db.session.delete(table)
                db.session.commit()
                return True, None, 204

            except Exception as e:
                print(e)
                return False, "Database error", 400

        else:
            return False, "A child table is protected", 422
    except Exception as e:
        print(e)
        return False, "An error occured", 400



def delete_API(db, api):
    """
        Deletes api.
    """
    tables = api.tables

    reference_ids = []
    table_ids = set([])
    for table in tables:
        reference_ids.append(table.reference.id)
        table_ids.add(table.id)

    stmt = db.select(TableParameter).where(TableParameter.foreign_key_reference_id.in_(reference_ids))
    child_table_params = db.session.scalars(stmt).all()

    try:

        can_delete = traverse_table_reference_child_tables(child_table_params, table_ids)

        
        if can_delete:
            try:
                db.session.delete(api)
                db.session.commit()
                return True, None, 204

            except Exception as e:
                print(e)
                return False, "Database error", 400

        else:
            return False, "A child table on one of the tables in this api is protected", 422

    except Exception as e:
        print(e)
        return False, "An error occured", 400

def delete_entrylists(db, fk_ref_table_id, entrylists):
    """
        Delete rows from a table.
    """

    print("fk_ref_table_id", fk_ref_table_id)
    print('entrylists', entrylists)
    stmt = db.select(TableParameter).where(TableParameter.foreign_key_reference_id == fk_ref_table_id)

    try:
        child_table_params = db.session.scalars(stmt).all()
        print('child_table_params', child_table_params)
        if not child_table_params:
            can_delete = True
        else:
            pks = [entrylist.primary_key_value for entrylist in entrylists]
            can_delete = traverse_table_ref_entrylist_child_tables(db, fk_ref_table_id, pks, child_table_params)

        if can_delete:
            try:
                e_ids = [entrylist.id for entrylist in entrylists]
                db.session.execute(db.delete(EntryList).where(EntryList.id.in_(e_ids)))
                db.session.commit()
                return True, None, 204
            except Exception as e:
                print(e)
                return False, "Database error", 400
        else:
            return False, "Protected child rows are present and can't be deleted", 422
        
    except RecursionError as e:
        return False, str(e), 409
    except Exception as e:
        print(e)
        return False, "An error occured", 400

