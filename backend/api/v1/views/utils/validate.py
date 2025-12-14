"""
This module contains series
of validation check helper functions.
"""


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
            value = secrets.randbelow(2001)
            if value < lowest_value:
                continue
        e = Entry.query.filter_by(tableparameter_id=tb_param.id, value=value).first()
        if not e:
            break

    return value

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
        print('got here', get_ref_table, fk)
        e_li = EntryList.query.filter_by(table_id=get_ref_table.table_id, primary_key_value = value).first()
        print('e_li', e_li)
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


def unique_constraints_validator():
    pass