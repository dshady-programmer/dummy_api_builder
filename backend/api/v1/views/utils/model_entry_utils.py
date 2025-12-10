
from models import db, Entry, EntryList, Relationship
from .validate import validate_entry_constraints, validate_entry_value, validate_entry_value_length
from dateutil.parser import parse
from .filtering_utils import query_filter
from .parsers import parse_value

def datetime_repr(entry_value, type):
    if type == "datetime":
        return str(parse(entry_value))
    elif type == "date":
        return str(parse(entry_value).date())
    return entry_value



def validate_create_fk_relationships(tbl_p, api_name, table_name, entry_name, entry_value, e_list, stat, err_msg):
    # rel_key is <foreign_ref_field>.childapi.table.field (see model definition)
    rel_key = f"{tbl_p.foreign_key_reference_field}->{api_name}.{table_name}.{entry_name}" # incase of foreign key
    foreignKey_model_name = f"{api_name.lower()}_{table_name.lower()}s" # reverse lookup key 
    if not stat:
        if not err_msg.startswith('Primary key'):
            rels = Relationship.query.filter_by(fk_rel=rel_key).all() # foreign key reference table is either deleted or updated.
        else:
            rels = Relationship.query.filter_by(fk_rel=rel_key, entry_ref_pk=entry_value).all()  # check if relationship already has a field referencing the foreign key table row
            if not rels:
                rels = None
        raise Exception({"error": err_msg, "relationships": rels})
    else:
        # if everything goes fine.. add the entrylist to a relationship using the foreign key primary key (if not already existing create new one) 
        try:
            relationship = Relationship.query.filter_by(fk_rel = rel_key, entry_ref_pk = entry_value, fk_model_name=foreignKey_model_name).first() 
            if not relationship:
                relationship = Relationship(entry_ref_pk=entry_value, fk_rel=rel_key, fk_model_name=foreignKey_model_name)
            relationship.entrylists.append(e_list)
            db.session.add(relationship)
        except:
            raise Exception({"error": "Could not reference the foreign key id"})



def validate_create_update_entry_items(entry, parameters, e_list, api_name, table, user, primary_key_fields, update=False):
    primary_keys = []
    for entry_name, entry_value in entry.items():
        if entry_name not in parameters:
            if update:
                continue
            raise Exception({"error": f"such field name '{entry_name}' doesn't exist"})
        tbl_p = parameters[entry_name]
        stat, const_type, err_msg = validate_entry_constraints(entry_value, tbl_p, user) # Validating the entry against the existing constraint
        if const_type == "nullable" and stat:
            continue # waive null value for nullable constraints
        if const_type == "fk":
            validate_create_fk_relationships(tbl_p, api_name, table.name, entry_name, entry_value, e_list, stat, err_msg)
        else:
            if not stat and const_type == "uniq":
                raise Exception({"error": err_msg})

            if not validate_entry_value(entry_value, tbl_p.data_type.name):
                raise Exception({"error": "Wrong data type passed."})
            
            if not validate_entry_value_length(entry_value, tbl_p.data_type.name, tbl_p.dataType_length):
                raise Exception({"error": f"max length of '{entry_name}' exceeded"})
        if tbl_p.primary_key:
            primary_keys.append({"id": tbl_p.id, "value": entry_value})
        if tbl_p.data_type.name == "datetime" or tbl_p.data_type.name == "date":
            entry_value = datetime_repr(entry_value, tbl_p.data_type.name)
        
        e = None
        if update:
            e = Entry.query.filter_by(tableparameter_id=tbl_p.id, entry_list_id=e_list.id).first() # Grab the entry to be updated
            if e:
                # If the entry exists update the value
                rel_key = f"{tbl_p.foreign_key_reference_field}->{api.name}.{table.name}.{entry_name}"
                relationship = Relationship.query.filter_by(fk_rel = rel_key, entry_ref_pk = e.value, fk_model_name=foreignKey_model_name).first() 
                # remove the previous value from the relationship before updating it
                if relationship:
                    relationship.entrylists.remove(e_list)
                e.value = entry_value 
                db.session.add(relationship)
                db.session.add(e)

        if not e:
            e = Entry(value=entry_value, tableparameter_id=tbl_p.id)
            e_list.entries.append(e)
    
    if not primary_keys and not update:
        raise Exception({"error", "No primary key value"})
    if primary_keys:
        # Merge all the primary keys to form the main primary key for the field.
        primary_keys_sorted = sorted(primary_keys, key=lambda x: x["id"])
        # get the ids to compare user provided primary keys to the actual table primary key value
        primary_key_ids = {k["id"] for k in primary_keys_sorted} # gets the ids of the sorted primary key dicts

        if primary_key_fields != primary_key_ids:
            raise Exception({"error": "Primary key field provided doesn't match with your table primary keys"})
        print("primary keys", primary_key_fields, primary_key_ids)
        primary_key_value = "".join([ str(key["value"]) for key in primary_keys_sorted])
        # check if primary key already exists
        if EntryList.query.filter_by(table_id=table.id, primary_key_value=primary_key_value).first():
            raise Exception({"error": "Primary key already exist"})
        e_list.primary_key_value = primary_key_value




def create_entry(table, entry, user, api_name):
    
    try:
        if type(entry) != dict:
            raise Exception({"error": "Entry must be a dictionary"})
        
  
        required_parameters = []
        parameters = {}
        primary_key_fields = set() # needed to ensure users don't create the wrong primary key
        for table_parameter in table.table_parameters:
            parameters[table_parameter.name] = table_parameter
            for c in table_parameter.constraints:
                if c.name.value == "nullable":
                    continue
                if c.name.value == "primary_key":
                    primary_key_fields.add(table_parameter.id)
                
            required_parameters.append(table_parameter)
        if len(entry) < len(required_parameters) or len(entry) > len(parameters):
            raise Exception({"error": "Incomplete field or a non declared field has been passed"})
        e_list = EntryList(table_id = table.id)
        db.session.add(e_list)

        """
        entry format
        
        {
            "_id": 1,
            "name": "Peter",
            "age": 18, 
            ...
        }
        
        """
        validate_create_update_entry_items(entry, parameters, e_list, api_name, table, user, primary_key_fields)

    except Exception as e:
        print(e)
        error = e.args[0]
        db.session.rollback()
        if type(error) == dict:
            if "relationships" in error:
                if error["relationships"]:
                    # clean the relationships for foreign keys
                    for stale_relationship in error["relationships"]:
                        stale_relationship.entrylists.clear()
                        db.session.delete(stale_relationship)
                    db.session.commit()
                error.pop("relationships")
                
            if "error" in error:
                return error 
        return {"error": "Something went wrong"}
    
    else:
        db.session.commit()
        return {entry.tableparameter.name: entry.value for entry in e_list.entries} 



def update_entry(entry, table, e_list, api_name, user):
    try:

        if type(entry) != dict:
            raise Exception({"error": "Entry must be a dictionary"})
        
        parameters = {}
        primary_key_fields = set() # needed to ensure users don't create the wrong primary key
        for table_parameter in table.table_parameters:
            parameters[table_parameter.name] = table_parameter
            for c in table_parameter.constraints:
                if c.name.value == "primary_key":
                    primary_key_fields.add(table_parameter.id)
        
        validate_create_update_entry_items(entry, parameters, e_list, api_name, table, user, primary_key_fields, True)      

    except Exception as e:
        print(e)
        error = e.args[0]
        db.session.rollback()
        if type(error) == dict:
            if "relationships" in error:
                if error["relationships"]:
                    # clean the relationships for foreign keys
                    for stale_relationship in error["relationships"]:
                        stale_relationship.entrylists.clear()
                        db.session.delete(stale_relationship)
                    db.session.commit()
                error.pop("relationships")
                
            if "error" in error:
                return error 
        return {"error": "Something went wrong"}
    
    else:
        db.session.commit()
        return {entry.tableparameter.name: entry.value for entry in e_list.entries} 







def list_entries(args, table):

    data = []
    try:

        if args:
            found_valid_arg = False # if params passed in are valid or not
            get_entryLists = EntryList.query.filter_by(table_id=table.id)
            for entry_list in get_entryLists:
                entry_data = {}
                get_entries = entry_list.entries
                filter_in = True
                for entry in get_entries:
                    tp_name = entry.tableparameter.name
                    e_value = parse_value(entry.tableparameter.data_type.name, entry.value)
                    found_valid_arg, filter_in = query_filter(tp_name, args, entry.tableparameter.data_type.name, entry.value)
                        
                    entry_data[tp_name] = e_value
                if filter_in:
                    data.append(entry_data)
            if found_valid_arg:
                return data
        data = []
        for entry_list in table.entry_lists:
            if entry_list.entries:
                data.append({entry.tableparameter.name: int(entry.value) if entry.tableparameter.data_type.name == "integer" else entry.value for entry in entry_list.entries})
    except Exception as e:
        print(e)
        return {"error": "Something went wrong"} 
    else:
        return data 
    

