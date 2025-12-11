"""
This module contains series
of validation check helper functions.
"""


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
    if len(name) < 3 or type(name) != str:
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
            eval_value = eval(value)
            assert(type(eval_value) == int)
        except:
            return False
    elif data_type == "boolean":
        try:
            eval_value = eval(value)
            assert(type(eval_value) == bool)
        except:
            return False
    elif data_type == "datetime":
        try:
            eval_value = parse(value)
            print(eval_value)
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


def validate_entry_constraints(value, tbl_p, user=None):
    fk = None
    consts = [const.name.value for const in tbl_p.constraints]
    if "nullable" in consts:
        if not value:
            return True, "nullable", None
    if "foreign_key" in consts:
        from models.table import Table
        from models.api import Api
        from models.tableparameter import TableParameter
        from models.entrylist import EntryList
        from models.relationship import Relationship
        get_ref_table = tbl_p.foreign_key_reference_table

        if not get_ref_table:
            return False, "fk", "Reference table doesn't exist"
        e_li = EntryList.query.filter_by(table_id=get_ref_table.table_id, primary_key_value = value).first()
        if not e_li:
            return False, "fk", "Primary key referenced for the foreign key doesn't exist"
        fk = "fk"
    if "unique" in consts:
        from models.entry import Entry
        if Entry.query.filter_by(tableparameter_id=tbl_p.id, value=value).first():
            return False, "uniq", f"{value} already exists in the database. It must be unique"
    return True, fk, None



def validate_primary_key_dtType(data_type):
    VALID_PRIMARY_KEY_DATATYPES = ["string", "text", "integer"]
    if data_type not in VALID_PRIMARY_KEY_DATATYPES:
        return False
    return True