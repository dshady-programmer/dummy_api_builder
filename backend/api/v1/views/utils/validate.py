"""
This module contains series
of validation check helper functions.
"""
from ast import literal_eval


def autogenerate_keys(tb_param):
    import uuid
    import secrets
    from models import Entry
    datatype = tb_param.data_type.name 
    value = None

    while True:
        if datatype in ["string", "text"]:
            value = str(uuid.uuid4())
        
        else:
            lowest_value = 1
            value = secrets.randbelow(2000001)
            if value < lowest_value:
                continue
        e = Entry.query.filter_by(tableparameter_id=tb_param.id, value=value).first()
        if not e:
            break

    return value

def retrieve_remaining_rows_limit(user):
    from .constants import MAX_ROW_FOR_USER

    apis = user.user_apis
    total_rows = 0
    for api in apis:
        for table in api.tables:
            total_rows += len(table.entry_lists)
    remaining_rows = MAX_ROW_FOR_USER - total_rows
    return remaining_rows

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
        "boolean",
        "date",
        "datetime"
    ]
    if type not in valid_types:
        return False
    return True


def validate_name(name):

    import keyword
    if not name:
        return False
    if type(name) != str or len(name) < 3:
        return False
    return name.isidentifier() and not keyword.iskeyword(name)



def validate_entry_value(value, data_type):
    from dateutil.parser import parse
    import datetime
    if not value:
        return False
    value = str(value)
    if data_type == "integer":
        try:
            eval_value = literal_eval(value)
            assert(type(eval_value) == int)
        except:
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


def validate_entry_constraints(value, tbl_p):
    fk = None
    default_value = None
    consts = [const.name.value for const in tbl_p.constraints]
    for c in ["default", "nullable"]:
        if c in consts:
            condition = (type(value) == str and not value) or (type(value) != bool and not value)
            if condition and c == "default":

                if tbl_p.primary_key:
                    # auto generate keys for primary keys
                    default_value = autogenerate_keys(tbl_p)
                    return True, c, None, default_value
                elif "foreign_key" in consts:
                    value = tbl_p.default_value # we need to ensure the default value exist.
                    fk = "default_fk"
                    default_value = str(value)
                    break
                else:
                    default_value = str(tbl_p.default_value)
            if condition:
                return True, c, None, default_value
        
    if (type(value) == str and not value) or (type(value) != bool and not value):
        return False, "non-nullable", "Value can't be empty", default_value

    value = str(value)
    if "foreign_key" in consts:
        from models.entrylist import EntryList

        if not fk:
            fk = "fk"
        get_ref_table = tbl_p.foreign_key_reference_table
      
        if not get_ref_table:
            return False, fk, "Reference table doesn't exist", default_value
        e_li = EntryList.query.filter_by(table_id=get_ref_table.table_id, primary_key_value = value).first()
        if not e_li:
            return False, fk, f"Primary key '{value}' referenced for the foreign key doesn't exist on the parent table", default_value
    if "unique" in consts:
        from models.entry import Entry
        if Entry.query.filter_by(tableparameter_id=tbl_p.id, value=value).first():
            return False, "uniq", f"{value} already exists in the database. It must be unique", default_value
    return True, fk, None, default_value



def validate_primary_key_dtType(data_type):
    VALID_PRIMARY_KEY_DATATYPES = ["string", "text", "integer"]
    if data_type not in VALID_PRIMARY_KEY_DATATYPES:
        return False
    return True


def unique_constraints_validator(table_param, nullable=False):
    entries = table_param.entries # get the entire column of existing values
    existing_values = set() # take advantage of the set data type for average 0(1) lookup
    for entry in entries:
        # condition if it has a nullable flag and but 
        condition = (entry.value and entry.value in existing_values)

        if condition:
            raise Exception({"error": "Failed unique constraints, more than one row with the same value"})
        elif nullable and not entry.value:
            continue
        elif not nullable and not entry.value:
            raise Exception({"error": "Found null values for a non-nullable column."})
        existing_values.add(entry.value)
    

def foreign_key_constraints_validator(parent_table, table_param, nullable=False):
    """
    
        Runs validation on all existing fields and ensure that they are valid keys

    """
    from models import EntryList
    entries = table_param.entries
    validated_keys = set()
    for entry in entries:

        condition = (entry.value and entry.value not in validated_keys)
        if condition:
            e_list = EntryList.query.filter_by(table_id=parent_table.id, primary_key_value=entry.value).first()
            if not e_list:
                raise Exception({"error": "Failed foreign key constraints, one or more rows does not reference a valid pk value on the parent table "})
        elif nullable and not entry.value:
            continue
        elif not nullable and not entry.value:
            raise Exception({"error": "Found null values for a non-nullable column"})
        
        validated_keys.add(entry.value)
        

def foreign_key_ref_table_validator(table_param, param_dt, param, user):
    
    from models import Api, Table, ForeignKeyFieldReferenceTable

    if not validate_primary_key_dtType(param_dt): # since foreign key would always reference a primary key of the parent table.. it should conform with the valid data types
        # you can use of a foreign with the data type int, string or text. It doesn't have to tie strictly the parent table primary key field datatype
        raise Exception({"error": "Foreign key data type must be either text, string or integer"})
    fk_rf = param.get("foreign_key_rf") #expected format(api.table)
    if not fk_rf:
        raise Exception({"error": "Expected a foreign key reference field."})
    f_api, f_table = fk_rf.split(".") # Check if the reference api and model are valid for it to be a foreign key field
    r_api = Api.query.filter_by(name=f_api, user_id=user.id).first()
    if not r_api:
        raise Exception({"error": "Api name referenced in the foreign key doesn't exist"})
    r_table = Table.query.filter_by(name=f_table, api_id=r_api.id).first()
    if not r_table:
        raise Exception({"error": "Table name referenced doesn't exist"})
    foreign_key_ref_table = ForeignKeyFieldReferenceTable.query.filter_by(table_id=r_table.id).first()
    table_param.foreign_key_reference_id = foreign_key_ref_table.id
    return r_table

def validate_foreign_key_default_value(
        parent_table, table, table_param, 
        default_value, entry_present, 
        run_update, update
    ):
    from models import EntryList
    from .model_entry_utils import (
        create_default_value_entries, 
        update_default_value_entries
    )

    if not default_value:
        return 

    e_list = EntryList.query.filter_by(table_id=parent_table.id, primary_key_value=default_value).first()
    if not e_list:
        raise Exception({"error": "FK default value does not reference a valid primary key value on the parent table"})
    table_param.default_value = default_value
    if entry_present:
        if not update:
            create_default_value_entries(table, table_param, default_value)

        elif update and run_update:
            update_default_value_entries(table_param, default_value)
            