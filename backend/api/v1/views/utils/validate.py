"""
This module contains series
of validation check helper functions.
"""
from ast import literal_eval

from models import (
    db, Entry, Relationship,
    Api, Table, EntryList,
    ForeignKeyFieldReferenceTable
)
from dateutil.parser import parse
import datetime
from sqlalchemy.orm import selectinload, joinedload
import keyword
import uuid
import secrets
from .parsers import datetime_repr
import math


def autogenerate_keys(tb_param, tracked_pks, bulk=False):
    datatype = tb_param.data_type.name 
    value = None

    while True:
        if datatype in ["string", "text"]:
            value = str(uuid.uuid4())
        
        else:
            lowest_value = 1
            value = secrets.randbelow(200000001)
            if value < lowest_value:
                continue
        if bulk and value not in tracked_pks:
            break

        elif not bulk:
            e = db.session.scalar(
                db.select(db.exists().where(Entry.tableparameter_id == tb_param.id, Entry.value == value))
            )
            if not e:
                break

    return value

# def retrieve_remaining_rows_limit(user):
#     from models.user import MAX_ROW_FOR_USER

#     apis = user.user_apis
#     total_rows = 0
#     for api in apis:
#         for table in api.tables:
#             total_rows += len(table.entry_lists)
#     remaining_rows = MAX_ROW_FOR_USER - total_rows
#     return remaining_rows

def validate_constraint(constraint):
    valid_constraints = [
        "foreign_key",
        "unique",
        "nullable",
        "primary_key",
        "default"
    ]
    if constraint not in valid_constraints:
        return False
    return True

def validate_dtType(type):
    valid_types = [
        "string",
        "text",
        "integer",
        "decimal",
        "boolean",
        "date",
        "datetime"
    ]
    if type not in valid_types:
        return False
    return True


def validate_name(name, tableparameter_field=False):

    if not name:
        return False
    if type(name) != str or (not tableparameter_field and len(name) < 3):
        return False

    if (len(name) > 50):
        return False
    return name.isidentifier() and name.isascii() and not keyword.iskeyword(name)



def validate_entry_value(value, data_type):
    if value is None or not str(value):
        return False
    value = str(value)
    if data_type == "integer":
        try:
            eval_value = literal_eval(value)
            assert(type(eval_value) == int)
        except:
            return False
        if not math.isfinite(eval_value): # rejects 'nan', 'inf'
            return False
    elif data_type == "decimal": # validate.py, validate_entry_value
        try:
            eval_value = literal_eval(value)
            assert(type(eval_value) == float)
        except:
            return False
        if not math.isfinite(eval_value): # rejects 'nan', 'inf'
            return False
    elif data_type == "boolean":
        try:
            eval_value = literal_eval(value)
            assert(type(eval_value) == bool)
        except:
            return False
    elif data_type == "datetime":
        try:
            eval_value = parse(value)
            assert(type(eval_value) == datetime.datetime)
        except:
            return False
    elif data_type == "date":
        try:
            eval_value = parse(value)
            assert(type(eval_value.date()) == datetime.date)
        except:
            return False
    return True


def validate_entry_value_length(value, type, length):
    if not length:
        return True
    if type == 'text' or type == 'string':
        return len(str(value)) <= length
    return True


def validate_entry_constraints(value, tbl_p, tracked_unique_values, tracked_fk_values, tracked_pks, bulk=False):
    fk = None
    default_value = None
    consts = [const.name.value for const in tbl_p.constraints]
    condition = value is None or (isinstance(value, str) and not value.strip())
    for c in ["default", "nullable"]:
        if c in consts:
            if condition and c == "default":

                if tbl_p.primary_key:
                    # auto generate keys for primary keys
                    default_value = autogenerate_keys(tbl_p, tracked_pks, bulk)
                elif "foreign_key" in consts:
                    # value = tbl_p.default_value # we need to ensure the default value exist.
                    fk = "default_fk"
                    
                    if tbl_p.foreign_key_default_value:
                        val = tbl_p.foreign_key_default_value.primary_key_value
                    else:
                        return False, fk, "foreign key default value isn't set", default_value
                    if val:
                        default_value = str(val)
                    else:
                        default_value = val
                    break
                elif tbl_p.data_type.name in ['date', 'datetime']:

                    if tbl_p.default_value == "created" or not tbl_p.default_value:
                        default_value = datetime_repr(str(datetime.datetime.now()), tbl_p.data_type.name)
                    else:
                        default_value = str(tbl_p.default_value)

                else:
                    default_value = str(tbl_p.default_value)

                return True, c, None, default_value
            elif condition and c == "nullable":
                return True, c, None, default_value
        
    if condition and not default_value:
        return False, "non-nullable", "Value can't be empty", default_value


    value = str(value) if value is not None else None

    if "foreign_key" in consts:

        if not value and fk == 'default_fk' and default_value is not None:
            fk_value = default_value
        else:
            fk_value = value

        if not fk:
            fk = "fk"

        if fk_value in tracked_fk_values["values"]:
            return True, fk, None, default_value
        
        get_ref_table = tbl_p.foreign_key_reference_table
      
        if not get_ref_table:
            return False, fk, "No Reference table", default_value
        
        if fk == "fk" or value: # could be default but still get value passed.. this should override
            # validate input field

            e_li = db.session.scalar(
                    db.select(EntryList).filter_by(table_id=get_ref_table.table_id, primary_key_value = value)
                )
        else:
            # default fk would be valid as far as there's a value
            if not default_value:
                return False, fk, "Foreign key default value is empty.", default_value

            e_li = tbl_p.foreign_key_default_value
        if not e_li:
            return False, fk, f"Primary key '{fk_value}' referenced for the foreign key doesn't exist on the parent table", default_value

        tracked_fk_values["values"][value] = e_li
    if "unique" in consts:
        if not tbl_p.primary_key:
            tracked_uniq = tracked_unique_values[tbl_p.id] if tbl_p.id in tracked_unique_values else []
            if value in tracked_uniq or db.session.scalar(db.select(Entry).filter_by(tableparameter_id=tbl_p.id, value=value)):
                return False, "uniq", f"{value} already exists in the database. It must be unique", default_value
    return True, fk, None, default_value



def validate_primary_key_dtType(data_type):
    VALID_PRIMARY_KEY_DATATYPES = ["string", "text", "integer"]
    if data_type not in VALID_PRIMARY_KEY_DATATYPES:
        return False
    return True

def validate_foreign_key_dType(data_type):
    VALID_FOREIGN_KEY_DATATYPES = ["string", "text"]
    if data_type not in VALID_FOREIGN_KEY_DATATYPES:
        return False
    return True

def unique_constraints_validator(table_param, nullable=False):
    entry_stmt = db.select(Entry).filter_by(tableparameter_id=table_param.id)
    entries = db.session.scalars(entry_stmt).all()
    entries = table_param.entries # get the entire column of existing values
    existing_values = set() # take advantage of the set data type for average 0(1) lookup
    for entry in entries:
 
        condition = (entry.value is not None and entry.value in existing_values)

        if condition:
            raise Exception({"error": "Failed unique constraints, more than one row with the same value"})
        elif nullable and entry.value is None:
            continue
        elif not nullable and entry.value is None:
            raise Exception({"error": "Found null values for a non-nullable column."})
        existing_values.add(entry.value)
    

def foreign_key_constraints_validator(parent_table, table_param, nullable=False):
    """
    
        Runs validation on all existing fields and ensure that they are valid keys

    """

    entry_stmt = db.select(Entry).filter_by(tableparameter_id=table_param.id).options(joinedload(Entry.entry_list))
    entries = db.session.scalars(entry_stmt).all()
    validated_keys = {}
    # db.session.scalar(db.select(EntryList).filter_by(table_id=parent_table.id, primary_key_value=entry.value))
    e_lists = db.session.scalars(db.select(EntryList).filter_by(table_id=parent_table.id)).all() # grab all the entries on the parent table 
    e_list_pks = set([e_list.primary_key_value for e_list in e_lists])

    for entry in entries:
        # first check the entries are valid primary key values on the parent table
        condition = (entry.value is not None and entry.value not in validated_keys)
        if condition:

            if entry.value not in e_list_pks:
                raise Exception({"error": "Failed foreign key constraints, one or more rows does not reference a valid pk value on the parent table "})
        elif nullable and entry.value is None:
            continue
        elif not nullable and entry.value is None:
            raise Exception({"error": "Found null values for a non-nullable column"})

        if validated_keys.get(entry.value):
            validated_keys[entry.value].append(entry.entry_list)
        else:
            validated_keys[entry.value] = [entry.entry_list]

    try:

        # Create a relationship and add the entrylist to the relationship
        # e_list = e_list_pks[entry.value]
        rels_stmt = db.select(Relationship)\
            .where(Relationship.foreign_key_rel_id == parent_table.reference.id, Relationship.entry_ref_pk.in_(validated_keys), Relationship.child_table_id == table_param.table_id)\
            .options(selectinload(Relationship.entrylists))
        relationships = db.session.scalars(rels_stmt).all()
        for relationship in relationships:
            e_lists = validated_keys[relationship.entry_ref_pk]
            for e_list in e_lists:
                if e_list not in relationship.entrylists:
                    relationship.entrylists.append(e_list)
            validated_keys.pop(relationship.entry_ref_pk)

        for entry_value, e_lists in validated_keys.items:
            
            rel = Relationship(entry_ref_pk=entry_value, foreign_key_rel_id=parent_table.reference.id,
                                child_table_id=table_param.table_id)
            rel.entrylists.extend(e_lists)
            db.session.add(rel)

    except:
        raise Exception({"error": "Could not reference the foreign key id while getting/creating relationship"})

        

def foreign_key_ref_table_validator(table_param, param_dt, param, user, validated_fks, entry_present):
    
    run_validator = False
    if not validate_foreign_key_dType(param_dt): # since foreign key would always reference a primary key from the parent table.. it should conform with the valid pk data types(excluding integers)
        # you can use a foreign with the data type string or text. It doesn't have to tie strictly to the parent table primary key field datatype
        # int is excluding because if the parent table type is a string (uuid for example) and the child table is set to be an int data type
                # then there's no way a uuid string would ever be coerced to an integer
        raise Exception({"error": "Foreign key data type must be either text or string"})
    table_param.dataType_length = None # no restriction to the maximum length to avoid any complications
    fk_ref = param.get("foreign_key_rf") #expected format(api.table)



    vfk = validated_fks["key_refs"].get(fk_ref, None) # check already validated foreign keys before blindly proceeding.

    if not vfk:
        if not fk_ref:
            raise Exception({"error": "Expected a foreign key reference field."})
        f_api, f_table = fk_ref.split(".", 1) # Check if the reference api and model are valid for it to be a foreign key field
        r_api = db.session.scalar(db.select(Api).filter_by(name=f_api, user_id=user.id))
        if not r_api:
            raise Exception({"error": "Api name referenced in the foreign key doesn't exist"})
        r_table = db.session.scalar(db.select(Table).filter_by(name=f_table, api_id=r_api.id))
        if not r_table:
            raise Exception({"error": "Table name referenced doesn't exist"})
        foreign_key_ref_table = db.session.scalar(db.select(ForeignKeyFieldReferenceTable).filter_by(table_id=r_table.id))

        fk_ref_id = foreign_key_ref_table.id

        validated_fks["key_refs"][fk_ref] = {"fk_ref_table": foreign_key_ref_table, "r_table": r_table}
    else:
        fk_ref_id = vfk['fk_ref_table'].id
        r_table = vfk['r_table']


    if entry_present and table_param.foreign_key_reference_id != fk_ref_id:
        # This is an update, check the previous foreign key ref id is the same as the current one
        # else revalidate the entire entries on the table.
        run_validator = True
    table_param.foreign_key_reference_id = fk_ref_id
    # print("table param", table_param, run_validator, fk_ref, fk_ref_id)
    return r_table, run_validator



def foreign_key_on_delete_validator(table_param, param, constraints):

    # check for primary key
    table_level_on_delete = param.get("table_level_on_delete")
    row_level_on_delete = param.get("row_level_on_delete")

    if table_level_on_delete not in ["protect", "cascade"] or row_level_on_delete not in ["protect", "cascade", "set_null"]:
        return None # defaults to protect for both row and table level

    if "primary_key" in constraints:
        table_level_on_delete = 'protect'
        if row_level_on_delete not in ['protect', 'cascade']:
            row_level_on_delete = 'protect'
    else:
        if row_level_on_delete == 'set_null' and "nullable" not in constraints:
            row_level_on_delete = 'protect'


    table_param.table_level_on_delete = table_level_on_delete
    table_param.row_level_on_delete = row_level_on_delete



def validate_foreign_key_default_value(
        parent_table, table, table_param, 
        default_value, entry_present, 
        run_update, update, validated_fks,
        is_default=False
    ):
    from .model_entry_utils import (
        create_default_value_entries, 
        update_default_value_entries
    )
    """
        Validate the default value passed against the foreign key table.

        It must match a valid primary key on the parent table..
        e.g parent table is "Company"

        child_table is "Car" with a field "make" referencing "Company".pk 

        "Company".pk must exist for it to be a valid foreign key.
        
    """
 

    if not is_default:
        return None

    key = f"{parent_table.id}-{default_value}"
    if not validated_fks["default_value_refs"].get(key):
        e_list = db.session.scalar(db.select(EntryList).filter_by(table_id=parent_table.id, primary_key_value=default_value))
        validated_fks["default_value_refs"][key] = e_list 
    else:
        e_list = validated_fks["default_value_refs"][key]
    if not e_list:
        raise Exception({"error": "FK default value does not reference a valid primary key value on the parent table"})
    table_param.default_value = default_value
    table_param.foreign_key_default_value_id = e_list.id
    if entry_present:
        if not update:
            create_default_value_entries(table, table_param, default_value, True)

        elif update and run_update:
            update_default_value_entries(table_param, default_value, True)





# def validate_and_update_pk_fk_parent_lock(constraints, prev_constraints, table_param):

#     from models import TableParameter
#     from sqlalchemy.exc import OperationalError

#     if all(["foreign_key" not in constraints, "foreign_key" not in prev_constraints]):
#         return None

#     tp_fk_ref_table = table_param.foreign_key_reference_table

#     if "foreign_key" in constraints and "primary_key" in constraints:
#         tp_fk_ref_table.table_reference.is_locked = True

#     elif "foreign_key" in prev_constraints and "primary_key" in prev_constraints:
#         if "primary_key" not in constraints or "foreign_key" not in constraints:
#             # first check if there are no longer tableparameter field with primary key still referencing the parent table 
#             # tp_stmt = db.select(TableParameter.id).where(
#             #     TableParameter.id != table_param.id, # exclude this due to uncommitted changes
#             #     TableParameter.foreign_key_reference_id == tp_fk_ref_table.id,
#             #     TableParameter.primary_key == True
#             #     # same as using the _and() or & 
#             #  ).exists() # possible race condition
#             try:
#                 tp_stmt = (
#                     db.select(TableParameter.id).where(
#                         TableParameter.id != table_param.id, # exclude this due to uncommitted changes
#                         TableParameter.foreign_key_reference_id == tp_fk_ref_table.id,
#                         TableParameter.primary_key == True
#                     ).with_for_update(nowait=True)
#                 )
#                 tp_row = db.session.scalar(tp_stmt)
#             except OperationalError:
#                 raise Exception({"error": "Request already in progress, try again"})

            
#             tp_fk_ref_table.table_reference.is_locked = tp_row is not None
        
