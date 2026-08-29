from models import (
    db, TableParameter,
    Api, Entry, Table,
    Constraint, Relationship, 
    ForeignKeyFieldReferenceTable
)
from sqlalchemy.orm import selectinload
from sqlalchemy import text

from .validate import (
    validate_constraint, validate_dtType, 
    validate_name, validate_primary_key_dtType, 
    validate_entry_value, validate_entry_value_length,
    unique_constraints_validator, foreign_key_ref_table_validator,
    validate_foreign_key_default_value,
    foreign_key_constraints_validator,
    foreign_key_on_delete_validator
)
import datetime


from .model_entry_utils import (
    create_null_value_entries, 
    create_default_value_entries, 
    update_default_value_entries
)
from .parsers import html_clean_value, datetime_repr


from .cache_utils import delete_cache, api_cache_namespace



def table_parameter_constraints_checks(
        table, table_param, param_dt, 
        param_dt_length, constraints, 
        entry_present, param_default_value, 
        prev_constraints, update
    ):
    
    
    if "primary_key" in constraints:
        if entry_present:
            if not update or (update and "primary_key" not in prev_constraints) :
                print('update', prev_constraints)
                raise Exception({"error": "Can't add new primary key field to a table with already existing data."})
            
        constraints.add("unique") # add unique to constraint if it's a primary key.
        if "nullable" in constraints:
            # You definitely can't have a field that is a PK and still allow a null value
            constraints.remove("nullable")
        if not validate_primary_key_dtType(param_dt):
            raise Exception({"error": "primary key data type must be either text, string or integer"})
    else:
        if entry_present and update and "primary_key" in prev_constraints:
            raise Exception({"error": "Can't remove an existing primary key field from a table with already existing data."})
        table_param.primary_key = False
    
        
        if update and entry_present and "unique" in constraints and "unique" not in prev_constraints:
            # only check unique constraints on existing table fields if the unique constraint wasn't present in previous constraints set
            # validate all entries in the table and ensure the field existing values are unique if it fails raise an error
            # check for nullable constraints is also done to exempt null values from unique constraint check 
            if "nullable" in constraints:
                unique_constraints_validator(table_param, True)
            else:
                unique_constraints_validator(table_param)        

        elif entry_present and not update and ("nullable" not in constraints or "default" not in constraints or "unique" in constraints):
            # if it's not an update and there is already data in the table, 
            # you can't add a new field without a default value or a nullable constraint 
            # since the existing entries won't have any value for the new field and that 
            # would violate the not null constraint. 
            #
            # Also you can't add a unique constraint without a default value 
            # or a nullable constraint since the existing entries won't have any value 
            # for the new field and that would violate the unique constraint
            constraints.add("nullable")
        
        if entry_present and "foreign_key" in constraints:
            if "default" not in constraints:
                # if there is already data in the table, you can't add a foreign key constraint 
                # without a default value or a nullable constraint
                constraints.add("nullable")


        if entry_present and not update and "nullable" in constraints and "default" not in constraints:
            # check if only nullable is present 
            # create entries if it's not update
            create_null_value_entries(table, table_param)
        



    if "default" in constraints:
        if "nullable" in constraints:
            constraints.remove("nullable")
        if "primary_key" not in constraints:
            if param_dt not in ["date", "datetime"] and not param_default_value:
                raise Exception({'error': 'Default constraint requires a default value to be provided'})
           
    
            if "unique" in constraints:
                # if there is a unique constraint on the field, 
                # we need to ensure that the default value doesn't violate the unique constraint
                constraints.remove("unique")
            if "foreign_key" not in constraints:
                # if there is no foreign key constraint, 
                # we can just create entries with the default value 
                # if there is already data in the table
                is_default_value_valid = validate_entry_value(param_default_value, param_dt)

                if param_dt not in ["date", "datetime"] and not is_default_value_valid:
                    raise Exception({"error": "Wrong data type passed for default value"})
                elif param_dt in ["date", "datetime"]:
                    if param_default_value != "created" and not is_default_value_valid:
                        param_default_value = None
                    elif is_default_value_valid:
                        param_default_value = datetime_repr(param_default_value, param_dt)
                    param_dt_length = None # don't validate length for datetime.
                    
                if not validate_entry_value_length(param_default_value, param_dt, param_dt_length):
                    raise Exception({"error": "Default values must obey max length restriction"})
                if entry_present:

                    if param_dt in ["date", "datetime"]:
                        if param_default_value == "created" or param_default_value is None:
                            d_value = datetime_repr(str(datetime.datetime.now()), param_dt)
                        else:
                            d_value = param_default_value
                    else:
                        d_value = param_default_value
                    if not update:
                        create_default_value_entries(table, table_param, d_value)
                    else:
                        update_default_value_entries(table_param, d_value)
                table_param.default_value = param_default_value


        else:
            # if it has primary key then the backend auto generates keys
            table_param.default_value = None # Ignore whatever value was set
            if "foreign_key" in constraints:
                # default, primary_key and foreign key constraints can't coexist (primary_key + default autogenerates unique values can cause unintended values with foreign key)
                raise Exception({"error": "A default primary key field can't also have a foreign key constraint"})
        
        # for update: update the existing entries to reflect the default value if not already existing (latest default value) 
        # create entries with the latest default values.
        
    if "foreign_key" not in constraints and table_param.foreign_key_reference_id is not None:
        table_param.foreign_key_reference_id = None








def check_and_validate_tableparameter(
        table, table_param, param, param_dt, param_dt_length, 
        param_default_value, constraints, user, entry_present, update=False
    ):

    primary_key_present = False
    prev_constraints = None
    if param_default_value is not None:
        param_default_value = html_clean_value(param_default_value)
        if param_dt == "boolean":
            param_default_value = param_default_value.capitalize() # ensure boolean values are capitalized for literal eval to work properly
    if update:
        prev_default_value = table_param.default_value
        prev_constraints = [c.name.value for c in table_param.constraints]
    
    table_parameter_constraints_checks(
        table, table_param,
        param_dt, param_dt_length,
        constraints, 
        entry_present, param_default_value, 
        prev_constraints, update
    )
           
        
    if update:
        table_param.constraints.clear()

    for const in constraints:
        # There can be more than one constraints for a model field
        if not validate_constraint(const):
            # Check if the constraint is valid
            raise Exception({"error": "invalid constraint"})
        if const == "foreign_key":
            parent_table = foreign_key_ref_table_validator(table_param, param_dt, param, user)
            foreign_key_on_delete_validator(table_param, param, constraints) # validate on delete options
            run_update = True
            is_default = "default" in constraints
            if entry_present and update:
                if prev_constraints and "foreign_key" in prev_constraints:
                    if is_default:
                        """
                        Don't bother running default validator check if the new default value is the same as the old
                        Provided the field remains a foreign key from previous update.
                        """
                        if prev_default_value and prev_default_value == param_default_value:
                            run_update = False 
                    else:
                        run_update = False
                else:
                    foreign_key_constraints_validator(parent_table, table_param, "nullable" in constraints)
            
            
            validate_foreign_key_default_value(
                parent_table, table, 
                table_param, param_default_value, 
                entry_present, run_update, update, is_default
            )

        if const == "primary_key":
            primary_key_present = True
            table_param.primary_key = True

        get_c = db.session.scalar(db.select(Constraint).filter_by(name=const))
    
        if get_c:
            table_param.constraints.append(get_c)
        else:
            table_param.constraints.append(Constraint(name=const))
    return primary_key_present

def create_table_parameter(param, table, tableparam_names, user, entry_present):
    
    param_name = param.get("name")
    param_dt = param.get("datatype")
    param_dt_length = param.get("dt_length")
    param_default_value = param.get("default_value", None)
    constraints = param.get("constraints") or []
    if type(constraints) != list:
        raise Exception({"error": "Invalid constraints type"})
    constraints = set(constraints) # incase of duplicate values.

    if not param_name:
        raise Exception({"error": "Table parameter name can't be empty"})
    if param_name in tableparam_names:
        # First check if the table param of such name already exist on the table
        """
        This check is done for events where table parameter is passed 2ce in the list
        just like there can't be two model columns of the same name
        e.g you can't have 
        name=String()
        and then..
        name = Integer()
        """
        
        raise Exception({"error": f"Duplicate name '{param_name}' of table parameter, it must be unique"})
    if not validate_dtType(param_dt):
        # validate the data type
        # Technically this check won't be triggered if the api is used from the frontend

        raise Exception({"error": "invalid data type"})
    if not validate_name(param_name, True):
        # validate the model field name
        # Technically this check won't be triggered if the api is used from the frontend
        raise Exception({"error": "invalid name(must be a valid python identifier) and not a python keyword"})
    try:
        if param_dt_length and param_dt in ["string", "text"]: # if maximum length is set for the model field
            # Ths would later be extended to data types like integer and decimals.
            param_dt_length = abs(int(param_dt_length))
        else:
            param_dt_length = None
    except ValueError: 
        # In case the param_dt_length passed is not an integer
        param_dt_length = None

    # If everything works perfectly go ahead and create the model field relating to the user table/model and the api
    p = TableParameter(name=param_name, data_type=param_dt, dataType_length=param_dt_length)
    table.table_parameters.append(p)
    # keep track of the param_name to avoid duplication later along the line
    tableparam_names.add(param_name)

    return check_and_validate_tableparameter(
                table, p, param, param_dt, 
                param_dt_length,
                param_default_value, constraints, 
                user, 
                entry_present
            )


def update_table_parameter(param,table, tableparam, tableparam_names, user, entry_present):
    param_name = param.get("name")
    param_dt = param.get("datatype")
    param_dt_length = param.get("dt_length")
    param_default_value = param.get("default_value", None)
    constraints = param.get("constraints") or []
    if type(constraints) != list:
        raise Exception({"error": "Invalid constraints type"})
    constraints = set(constraints) # incase of duplicate values.
   
    

    # check & update the param name
    if param_name:
        if param_name not in tableparam_names and validate_name(param_name, True):
            tableparam.name = param_name
            tableparam_names.add(param_name)

    if param_dt and validate_dtType(param_dt):
        if entry_present and tableparam.data_type.name != param_dt and param_dt not in ["string", "text"]:
            raise Exception({"error": f"'{tableparam.name}' table parameter data type can't be changed from {tableparam.data_type.name} to {param_dt} with rows present in the table"})
        elif entry_present and tableparam.data_type.name != param_dt and "primary_key" in tableparam.constraints:
            # it affects foreign key relationships.
            # would check if i can improve this..
            raise Exception({"error": "You can't change the data type of a primary key on a table with rows"})
        tableparam.data_type = param_dt
    
    if param_dt_length and param_dt in ["string", "text"]:

        try:
            param_dt_length = abs(int(param_dt_length))
            if entry_present and tableparam.dataType_length > param_dt_length:
                # If an entry is present compare the new datatype_length with the previous
                # previous mustn't be greater than new datatype_length
                # why? because reducing it might mean you might be violating some constraints..
                # It lazily just prevents you rather than validating each data against the new length which might be extra work
                raise Exception({"error": "You can't set a new max length to be less than the previous max length, there are already entries in this table"})

            if not param_dt_length:
                # In the case of 0 just set it to none..
                # What good is a field if the max length is 0?
                # None being no constraints
                tableparam.dataType_length = None
                raise ValueError
        
            tableparam.dataType_length = param_dt_length
        except ValueError:
            pass
    else:
        tableparam.dataType_length = None
            

    return check_and_validate_tableparameter(
            table, tableparam, param, param_dt,
            param_dt_length, 
            param_default_value, constraints, 
            user, 
            entry_present, True
        )


def delete_table_parameter(table_params):
    for _, table_param in table_params.items():
        table_param.constraints.clear()
        db.session.delete(table_param) # it should delete all entries 
        fk_ref_table_id = table_param.foreign_key_reference_id
        if fk_ref_table_id:
            Relationship.query.filter_by(foreign_key_rel_id=fk_ref_table_id).delete()

    ## cache update here too



def parse_and_create_tableparameters(table_parameters, new_table, user):
    primary_key_present = False

    tableparam_names = set()
    try:
        for param in table_parameters:
           is_primary_key = create_table_parameter(param, new_table, tableparam_names, user, False)
           if not primary_key_present:
               primary_key_present = is_primary_key
        if not primary_key_present:
            raise Exception({"error": "Table must contain atleast one primary key"})
    except Exception as e:
        print(e)
        # import traceback
        # traceback.print_exc()
        error = e.args[0]
        db.session.rollback()
        if type(error) == dict and "error" in error:
            return error 
        return {"error": "Something went wrong"}
    
    else:
        key = f"{api_cache_namespace(user.id, new_table.api_id)}:detail"
        delete_cache(key)
        db.session.commit()
        return {"id": new_table.id, "name": new_table.name, "desc": new_table.description}




def parse_and_update_tableparameters(table_parameters, table, user, entry_present):
    primary_key_present = False

    tableparam_names = set()
    existing_table_parameter_mapper = {}



    existing_primary_keys = set()
    updated_primary_keys = set()

    for existing_tblp in table.table_parameters:
        if existing_tblp.primary_key:
            existing_primary_keys.add(existing_tblp)
        tableparam_names.add(existing_tblp.name)
        existing_table_parameter_mapper[existing_tblp.id] = existing_tblp
    

    try:
        for param in table_parameters:
            param_id = param.get("index")
            if param_id in existing_table_parameter_mapper:
                is_primary_key = update_table_parameter(param, table, existing_table_parameter_mapper[param_id], tableparam_names, user, entry_present)
                if is_primary_key:
                    updated_primary_keys.add(existing_table_parameter_mapper[param_id])
                existing_table_parameter_mapper.pop(param_id)
            else:

                is_primary_key = create_table_parameter(param, table, tableparam_names, user, entry_present)
                # if is_primary_key and entry_present are true validation error is raised before getting to this point.
            if not primary_key_present:
                primary_key_present = is_primary_key
        if not primary_key_present:
            raise Exception({"error": "Table must contain atleast one primary key"})

        if entry_present and existing_primary_keys != updated_primary_keys:
            raise Exception({"error":  "You can't delete a primary key field from a table with already existing data."})
        
        delete_table_parameter(existing_table_parameter_mapper)
    except Exception as e:
        print(e)
        # import traceback
        # traceback.print_exc()
        error = e.args[0]
        db.session.rollback()
        if type(error) == dict and "error" in error:
            return error 
        return {"error": "Something went wrong"}
    
    else:
        db.session.commit()
        return {"id": table.id, "name": table.name, "desc": table.description}



# def delete_table(table):
#     """
#         When a foreign key field is also set as the primary key field there's need to lock the parent table
#             To prevent deletion of the child field when the parent table is deleted.
        
#         The lock acts like a ondelete="PROTECT"

#         This check kicks in when a table is about to be deleted.

#         This checks all the direct and indirect descendants of the tables that references it as a primary key.
#     """


#     dialect = db.engine.dialect.name

#     # get all table reference id where the tableparameter foreign key id is the fk_tb_ref_id..
#     # This gets all direct child table reference fk_tb_ref_id
#     # e.g User => Post => Comment
#     # if fk_tb_ref_id = user1.reference.id then base returns Post reference table.. because it's the only table 
#             # that has User has its foreign key
#     # The recursive query, repeats the same check from joining base.. since base returns the Post reference table
#     # the recursive now returns Comment reference table since comment is the only table that has Post has its foreign key
#     # Using common table expression with a recursive call to drill down the chain of parent->child relationship

#     # finally, lock all table reference rows that are direct or indirect descendants of table.reference.id

#     if dialect == 'postgresql':

#         all_ref_stmt = text(
#             """
#                 WITH RECURSIVE all_referencing  AS (
#                     SELECT table_ref.id AS table_ref_id, ARRAY[table_ref.id] AS path
#                         FROM tableparameter tp
#                             JOIN foreignkeyfieldreferencetable table_ref 
#                             ON table_ref.table_id = tp.table_id
#                         WHERE tp.foreign_key_reference_id = :parent_ref_id
                
#                     UNION ALL

#                     SELECT table_ref.id, all_ref.path || table_ref.id
#                         FROM tableparameter tp
#                             JOIN foreignkeyfieldreferencetable table_ref
#                                 ON table_ref.table_id = tp.table_id
#                             JOIN all_referencing all_ref
#                                 ON tp.foreign_key_reference_id = all_ref.table_ref_id
#                         WHERE tp.foreign_key_reference_id != ALL(all_ref.path)
            
#                 )
                
#                 SELECT tp.primary_key
#                 FROM foreignkeyfieldreferencetable fk_ref_table
#                     JOIN all_referencing all_ref ON fk_ref_table.id = all_ref.table_ref_id
#                     JOIN "table" t ON fk_ref_table.table_id = t.id
#                     JOIN tableparameter tp ON tp.table_id = t.id
#                 WHERE tp.foreign_key_reference_id IS NOT NULL
#                 FOR UPDATE OF fk_ref_table

#             """
#         )
#     elif dialect == 'mysql':
#         all_ref_stmt = text(
#             """
#                 WITH RECURSIVE all_referencing  AS (
#                     SELECT table_ref.id AS table_ref_id, CONCAT(',', table_ref.id, ',') AS path
#                         FROM tableparameter tp
#                             JOIN foreignkeyfieldreferencetable table_ref 
#                             ON table_ref.table_id = tp.table_id
#                         WHERE tp.foreign_key_reference_id = :parent_ref_id
                
#                     UNION ALL

#                     SELECT table_ref.id, CONCAT(all_ref.path, table_ref.id, ',')
#                         FROM tableparameter tp
#                             JOIN foreignkeyfieldreferencetable table_ref
#                                 ON table_ref.table_id = tp.table_id
#                             JOIN all_referencing all_ref
#                                 ON tp.foreign_key_reference_id = all_ref.table_ref_id
#                         WHERE INSTR(all_ref.path, CONCAT(',', table_ref.id, ',')) = 0
#                 )

#                 SELECT tp.primary_key
#                 FROM foreignkeyfieldreferencetable fk_ref_table
#                     JOIN all_referencing all_ref ON fk_ref_table.id = all_ref.table_ref_id
#                     JOIN "table" t ON fk_ref_table.table_id = t.id
#                     JOIN tableparameter tp ON tp.table_id = t.id
#                 WHERE tp.foreign_key_reference_id IS NOT NULL
#                 FOR UPDATE OF fk_ref_table
#             """
#         )
#     else:
#         # sqlite
#         all_ref_stmt = text(
#             """
#                 WITH RECURSIVE all_referencing  AS (
#                     SELECT table_ref.id AS table_ref_id, ',' || table_ref.id || ',' AS path
#                         FROM tableparameter tp
#                             JOIN foreignkeyfieldreferencetable table_ref 
#                             ON table_ref.table_id = tp.table_id
#                         WHERE tp.foreign_key_reference_id = :parent_ref_id
                
#                     UNION ALL

#                     SELECT table_ref.id, all_ref.path || table_ref.id || ','
#                         FROM tableparameter tp
#                             JOIN foreignkeyfieldreferencetable table_ref
#                                 ON table_ref.table_id = tp.table_id
#                             JOIN all_referencing all_ref
#                                 ON tp.foreign_key_reference_id = all_ref.table_ref_id
#                         WHERE INSTR(all_ref.path, ',' || table_ref.id || ',') = 0
#                 )

#                 SELECT tp.primary_key
#                 FROM foreignkeyfieldreferencetable fk_ref_table
#                     JOIN all_referencing all_ref ON fk_ref_table.id = all_ref.table_ref_id
#                     JOIN "table" t ON fk_ref_table.table_id = t.id
#                     JOIN tableparameter tp ON tp.table_id = t.id
#                 WHERE tp.foreign_key_reference_id IS NOT NULL

#             """
#         )

    

    
# # 
#     # all_ref_stmt += text("""
#     #     SELECT tp.primary_key
#     #         FROM foreignkeyfieldreferencetable fk_ref_table
#     #             JOIN all_referencing all_ref ON fk_ref_table.id = all_ref.table_ref_id
#     #             JOIN tableparameter tp ON tp.foreign_key_reference_id = fk_ref_table.id
#     #         FOR UPDATE OF fk_ref_table
#     # """)

#     all_descendants = db.session.scalars(all_ref_stmt, {"parent_ref_id": table.reference.id}).all()

#     # print('all descendants', all_descendants)
#     has_table_parameter_with_pk = any(all_descendants)

#     if has_table_parameter_with_pk:
#         db.session.rollback()
#         return False, f"Cannot delete {table.name}: At least one table is referencing it as primary key through a foreign key relationship"

#     db.session.delete(table)
#     db.session.commit()
#     return True, None

        



    
# def delete_API(api):
#     """
#         Same idea from `delete_table(table)`, but now we are checking from the api level.

#         if atleast one the tables are referenced as a foreign key and primary key then the API should be protected from deletion
#     """

#     table_ids = [t.id for t in api.tables]
#     # Lock ForeignKeyFieldReferenceTables and prevent Tableparameters from being attached while doing this check
#     fktable_refs_lock =  db.select(ForeignKeyFieldReferenceTable).where(ForeignKeyFieldReferenceTable.table_id.in_(table_ids)).with_for_update()
#     fktables = db.session.scalars(fktable_refs_lock).all()

#     fktable_ids = [fk_t.id for fk_t in fktables]

#     # Check if any of this table foreign key reference is being referenced by another table as their primary key
#     has_fk_as_pk_on_any = db.session.scalar(db.select(
#         db.exists().where(TableParameter.foreign_key_reference_id.in_(fktable_ids), TableParameter.primary_key == True)
#     ))

#     if has_fk_as_pk_on_any:
#         db.session.rollback()
#         return False, f"Cannot delete {api.name}: At least one table is referencing a table on this api via a foreign key relationship and having it as a primary key"


#     db.session.delete(api)
#     db.session.commit()
#     return True, None 


"""

   # Lock ForeignKeyFieldReferenceTable and prevent Tableparameters from being attached while doing this check 
    fktable_ref_lock = db.select(ForeignKeyFieldReferenceTable).where(ForeignKeyFieldReferenceTable.table_id == table.id).with_for_update()

    fktable = db.session.scalar(fktable_ref_lock)

    # Now check if any tableparameter as this reference table as foreign key and primary key
    has_fk_as_pk = db.session.scalar(db.select(
        db.exists().where(TableParameter.foreign_key_reference_id == fktable.id, TableParameter.primary_key == True)
    ))


    if has_fk_as_pk:
        db.session.rollback()
        return False, f"Cannot delete {table.name}: At least one table is referencing it as primary key through a foreign key relationship"

    db.session.delete(table)
    db.session.commit()
    return True, None
"""


"""
    `delete_table`

    fk_tb_ref_id = table.reference.id

    # get all table reference id where the tableparameter foreign key id is the fk_tb_ref_id..
    # This gets all direct child table reference fk_tb_ref_id
    # e.g User => Post => Comment
    # if fk_tb_ref_id = user1.reference.id then base returns Post reference table.. because it's the only table 
            # that has User has its foreign key
    base = (
        db.select(TableParameter.table.reference.label("table_ref_id")).where(
            TableParameter.foreign_key_reference_id == fk_tb_ref_id
        )
    )

    # The recursive query, repeats the same check from joining base.. since base returns the Post reference table
        # the recursive now returns Comment reference table since comment is the only table that has Post has its foreign key

    recursive = (
        db.select(TableParameter.table.reference.label("table_ref_id")).join(
            base, TableParameter.foreign_key_reference_id == base.c.table_ref_id
        )
    )

    # Using common table expression with a recursive call to drill down the chain of parent->child relationship
    all_referencing = db.union_all(base, recursive).cte(recursive=True)

    # lock all table reference rows that are direct or indirect descendants of table.reference.id

    all_descendants = db.session.scalars(
        db.select(ForeignKeyFieldReferenceTable).where(
            ForeignKeyFieldReferenceTable.id.in_(db.select(all_referencing.c.table_id))
        ).options(selectinload(ForeignKeyFieldReferenceTable.table_parameter_references)).with_for_update()
    ).all()

    has_table_parameter_with_pk = any([t.primary_key for t in tableparameters for tableparameters in all_descendants.table_parameter_references])

    if has_table_parameter_with_pk:
        db.session.rollback()
        return False, f"Cannot delete {table.name}: At least one table is referencing it as primary key through a foreign key relationship"

    db.session.delete(table)
    db.session.commit()
    return True, None

"""

