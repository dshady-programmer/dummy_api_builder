
from models import db, Entry, EntryList, Relationship
from .validate import validate_entry_constraints, validate_entry_value, validate_entry_value_length
from .filtering_utils import query_filter
from .parsers import parse_value, html_clean_value
from .cache_utils import invalidate_user_cache_api, get_cache, set_cache, set_raw_cache, get_raw_cache
from sqlalchemy.orm import selectinload
from .parsers import datetime_repr, datetime_parse
from .filtering_utils import generate_suffixes
import datetime



def validate_create_fk_relationships(tbl_p, entry_value, e_list, stat, err_msg):

    rel_id = tbl_p.foreign_key_reference_id
    child_table_id = tbl_p.table_id
    if not stat:
        raise Exception({"error": err_msg})
    else:
        # if everything goes fine.. add the entrylist to a relationship using the foreign key primary key (if not already existing create new one) 
        try:
            relationship = db.session.scalar(
                db.select(Relationship).filter_by(foreign_key_rel_id = rel_id, entry_ref_pk = entry_value, child_table_id=child_table_id)
            )
            if not relationship:
                relationship = Relationship(entry_ref_pk=entry_value, foreign_key_rel_id=rel_id, child_table_id=child_table_id)
                db.session.add(relationship)
                # parent_table = tbl_p.foreign_key_reference_table.table_reference
                # invalidate_user_cache_api(None, parent_table.api_id, parent_table.name , []) # invalidate the parent table cache for new relationships.. (old relationships would already be tracked)
            relationship.entrylists.append(e_list)
            return relationship
        except:
            raise Exception({"error": "Could not reference the foreign key id"})



def validate_create_update_entry_items(entry, parameters, e_list, table, primary_key_fields, tracked_pks=set(), tracked_unique_values={}, update=False):
    primary_keys = []
    tracked_changes = []
    pending_unique_changes = {}
    validated_entry_state = {}
    for entry_name, entry_value in entry.items():
        if entry_name not in parameters:
            if update:
                continue
            raise Exception({"error": f"such field name '{entry_name}' doesn't exist"})
        tbl_p = parameters[entry_name]
        if type(entry_value) == str:
            entry_value = entry_value.strip()
        stat, const_type, err_msg, default_return_value = validate_entry_constraints(entry_value, tbl_p, tracked_pks, tracked_unique_values) # Validating the entry against the existing constraint
        if const_type == "default" and stat:
            entry_value = default_return_value # set default value
        elif const_type == "nullable" and stat:
            if not update:
                continue # waive null value for nullable constraints

            entry_value = default_return_value

        if const_type == "non-nullable" and not stat: # passes empty string
            raise Exception({"error": err_msg})
        
        entry_value = str(entry_value) if entry_value is not None else entry_value # convert to a string since all values are stored as text in the database with the exception of None values which is acceptable for nullable fields (Note: this will only be triggered for "update" actions)
        if tbl_p.data_type.name == "boolean":
            entry_value = entry_value.capitalize() # ensure boolean values are capitalized for literal eval to work properly
        if const_type == "fk" or const_type == "default_fk":
            if const_type == "default_fk":
                entry_value = default_return_value
            rel = validate_create_fk_relationships(tbl_p, entry_value, e_list, stat, err_msg)
            tracked_changes.append(rel)
        else:
            if not stat and const_type == "uniq":
                raise Exception({"error": err_msg})
            if stat and const_type == "uniq":
                pending_unique_changes[tbl_p.id] = entry_value

            if entry_value and not validate_entry_value(entry_value, tbl_p.data_type.name):
                raise Exception({"error": "Wrong data type passed."})
            
            if entry_value and not validate_entry_value_length(entry_value, tbl_p.data_type.name, tbl_p.dataType_length):
                raise Exception({"error": f"max length of '{entry_name}' exceeded"})
        entry_value = html_clean_value(entry_value) if entry_value is not None else entry_value # clean html value to avoid xss attacks with the exception of None values which is acceptable
        if tbl_p.primary_key:
            if entry_value is None:
                # Not technically going to reach this point just an extra / redundant safeguard incase of shortcomings
                raise Exception({"error": "Primary key value can't be null"})
            primary_keys.append({"id": tbl_p.id, "value": entry_value})
        if tbl_p.data_type.name == "datetime" or tbl_p.data_type.name == "date":
            entry_value = datetime_repr(entry_value, tbl_p.data_type.name) if entry_value is not None else entry_value
        e = None
        if update:
            
            e = db.session.scalar(
                    db.select(Entry).filter_by(tableparameter_id=tbl_p.id, entry_list_id=e_list.id)
                ) # Grab the entry to be updated
            if e:
                e.value = entry_value
            tracked_changes.append(e)


        if not e:
            e = Entry(value=entry_value, tableparameter_id=tbl_p.id)
            e_list.entries.append(e)
        
        parameters.pop(entry_name) # remove already processed entry_name

        validated_entry_state[entry_name] = entry_value
        
    if not primary_keys and not update:
        raise Exception({"error": "No primary key value"})
    if primary_keys:
        # Merge all the primary keys to form the main primary key for the field.
        primary_keys_sorted = sorted(primary_keys, key=lambda x: x["id"])
        # get the ids to compare user provided primary keys to the actual table primary key value
        primary_key_ids = {k["id"] for k in primary_keys_sorted} # gets the ids of the sorted primary key dicts

        if primary_key_fields != primary_key_ids:
            raise Exception({"error": "Primary key field provided doesn't match with your table primary keys"})
        primary_key_value = "".join([ str(key["value"]) for key in primary_keys_sorted])
        # check if primary key already exists
        
        if primary_key_value in tracked_pks or db.session.scalar(
                db.select(EntryList).filter_by(table_id=table.id, primary_key_value=primary_key_value)
            ):
            raise Exception({"error": "Primary key already exist"})
        
        # Check if this primary key is already associated with a relationship
       
        if update:
            relationships = db.session.scalar(
                db.select(Relationship).filter_by(entry_ref_pk=e_list.primary_key_value, foreign_key_rel_id=table.reference.id).options(
                    selectinload(Relationship.entrylists
                ))
            )
            for relationship in relationships:
                if relationship:
                    # incase of update entries with active references can't be updated..
                    # can be updated without active references
                    if len(relationship.entrylists):
                        raise Exception({"error": "Primary key value is being used by other child table"})

                    # invalidate_user_cache_api(None, relationship.child_table.api.id, relationship.child_table.name, []) # invalidate any cache associated with the child table
                    # db.session.delete(relationship)
                
        e_list.primary_key_value = primary_key_value
        return tracked_changes, pending_unique_changes, validated_entry_state





def create_entry(table, entry, tracked_pks, 
                 tracked_unique_values, 
                 cached_required_parameters, 
                 cached_parameters, 
                 cached_primary_key_fields,
                 cached_default_pk_fields
                 ):

    """
        entry format
        
        {
            "_id": 1,
            "name": "Peter",
            "age": 18, 
            ...
        }
        
    """

    def load_field_tracker():
        for table_parameter in table.table_parameters:
            parameters[table_parameter.name] = table_parameter
            cached_parameters[table_parameter.name] = table_parameter
            required = True
            for c in table_parameter.constraints:
                if c.name.value == "nullable" or c.name.value == "default":
                    required = False
                if c.name.value == "primary_key":
                    primary_key_fields.add(table_parameter.id)
                    cached_primary_key_fields.add(table_parameter.id)
                    for _c in table_parameter.constraints:
                        # check if default constraint is present along side primary key so it can autogenerate a value.
                        # this step is necessary because the primary key field is a required parameter regardless of whether default constraint or not.
                        if _c.name.value == "default":
                            if table_parameter.name not in entry:
                                entry[table_parameter.name] = None
                                cached_default_pk_fields[table_parameter.name] = None
                            required = True
                            break
            if required:   
                required_parameters.append(table_parameter)
                cached_required_parameters.append(table_parameter)
    
    try:
        
        tracked_changes = []
        if type(entry) != dict:
            raise Exception({"error": "Entry must be a dictionary"})
        

        if any([cached_required_parameters, cached_parameters, cached_primary_key_fields]):
            required_parameters = cached_required_parameters.copy()
            parameters = cached_parameters.copy()
            primary_key_fields = cached_primary_key_fields.copy()
            
            # Primary key with default constraints might not be passed, to avoid validation error fill the entry with none
            for k, v in cached_default_pk_fields.items():
                if k not in entry:
                    entry[k] = v

        else:
            required_parameters = []
            parameters = {}
            primary_key_fields = set() # needed to ensure users don't create entries without all the primary key fields present

            load_field_tracker()



        if len(entry) < len(required_parameters) or len(entry) > len(parameters):
            # this doesn't effectively validate against absence of non-nullable fields...
            raise Exception({"error": "Incomplete field or a non declared field has been passed"})
        e_list = EntryList(table_id = table.id)


        
        t_changes, pending_unique_changes, v_entry_state = validate_create_update_entry_items(entry, parameters, e_list, table, primary_key_fields, tracked_pks, tracked_unique_values)
        tracked_changes.extend(t_changes)
        # after all the required parameters have been sorted
        # iterate over the remaining parameters and create an entry for them with null values and also ensure they do have nullable constraints on their respective fields (thus validating that non-nullable fields are indeed passed)
        for tb_param_name, tb_param  in parameters.items():
            tbl_constraints = [c.name.value for c in tb_param.constraints]
            if "nullable" in tbl_constraints or "default" in tbl_constraints:
                stat, const_type, err_msg, default_return_value = validate_entry_constraints(None, tb_param, tracked_pks, tracked_unique_values)
                if "default" in tbl_constraints:
                    if const_type == "default_fk":
                        rel = validate_create_fk_relationships(tb_param, default_return_value, e_list, stat, err_msg)
                        tracked_changes.append(rel)
                    e = Entry(tableparameter_id=tb_param.id, value=default_return_value)
                    e_value = default_return_value
                else:
                    e = Entry(tableparameter_id=tb_param.id)
                    e_value = None

                v_entry_state[tb_param_name] = e_value
                e_list.entries.append(e)
            else:
                raise Exception({"error": f"{tb_param_name} is a non-nullable field (can't be empty)"})

        

    except Exception as e:
        print(e)
        
        for change in tracked_changes:
            db.session.expunge(change)
        error = e.args[0]

        if type(error) == dict:
            if "error" in error:
                return error 
        return {"error": "Something went wrong"}
    
    else:

        db.session.add(e_list)
        db.session.add_all(tracked_changes)

        for k, v in pending_unique_changes.items():
            tracked_unique_values[k] = tracked_unique_values.get(k, []) + [v]
        tracked_pks.add(e_list.primary_key_value)
        return {tb_param_name: parse_value(cached_parameters[tb_param_name], value) for tb_param_name, value in v_entry_state.items()} 



def update_entry(entry, table, e_list):
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
        
        validate_create_update_entry_items(entry, parameters, e_list, table, primary_key_fields, update=True)      

        # extra iteration to check for date or datetime fields for update:
        for tbl_p in table.table_parameters:
            if tbl_p.data_type.name in ['date', 'datetime']:
                if not tbl_p.default_value: # only update if the default value is empty.
                    now = datetime_repr(str(datetime.datetime.now()), tbl_p.data_type.name)
                    for e in e_list.entries:
                        if e.tableparameter_id == tbl_p.id:
                            e.value = now
                            break
                


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
        return {entry.tableparameter.name: parse_value(entry.tableparameter, entry.value) for entry in e_list.entries} 





def return_entry_data(page, size, offset, runningSize, runningOffset, data):
    if page:
        has_next = runningSize < 0
        has_prev = page > 1
        next_num = page + 1 if has_next else None
        prev_num = (offset - runningOffset) / size if has_prev else None
        total_data = len(data)
        return {"data": data, "page": page, "has_next": has_next, "has_prev": has_prev, "next_page_num": next_num, "prev_page_num": prev_num, "total_entries": total_data}

    return {"data": data}



def build_entry_array(entrylists):
    """
        Load entrylist from database
            and
        Build an array of entrylists
    
    """
    data = []
    data_type_map = {}
    for entrylist in entrylists:
        entry_data = {}
        entries = entrylist.entries
        for entry in entries:
            tp_name = entry.tableparameter.name
            e_value = parse_value(entry.tableparameter, entry.value)
            entry_data[tp_name] = e_value
            if tp_name not in data_type_map:
                data_type_map[tp_name] = entry.tableparameter.data_type.name
        data.append(entry_data)

    return data, data_type_map


def build_entry_filter(entrylist_array, data_type_map, args, filter_type="&"):
    """
        Filter the entrylist array based on any arg param passed

        filter_type default is "&"
    """
    if not args:
        return entrylist_array
    
    if len(entrylist_array) == 0:
        return entrylist_array
    tp_names = list(data_type_map.keys())
    valid_args = []

    found_tp_names = set()

    for tp_name in tp_names:
        for tp_suffix in generate_suffixes(tp_name):
            if tp_name not in found_tp_names and tp_suffix in args:
                found_tp_names.add(tp_name) # filter out multiple suffixes for the same table parameter name
                arg = {}
                arg['tp_name'] = tp_name
                arg["tp_suffix"] = tp_suffix
                valid_args.append(arg)
                
    filtered_array = []
    for entrylist in entrylist_array:
        filtered_in = query_filter(entrylist, valid_args, args, data_type_map, filter_type)
        if filtered_in:
            filtered_array.append(entrylist)
    
    return filtered_array

def build_entry_ordering(entrylist_array, data_type_map, order_by):
    """
        Sort or order entry list array by keys
    """
    if not order_by:
        return entrylist_array

    valid_ordering = []

    tp_names = set(data_type_map.keys())
    order_by = order_by[:len(tp_names)]

    for order in order_by:
        tp_order = order
        if order.startswith('-'):
            tp_order = order[1:]
        if tp_order in order_by:
            valid_ordering.append(order)

    end = len(valid_ordering) - 1

    sorted_entrylist_array = entrylist_array

    def sort_key(entrylist, sort_by):
        datatype = data_type_map[sort_by]
        value = entrylist[sort_by]
        if datatype == "string" or datatype == "text":
            return str(value).lower() if value is not None else ""
        elif datatype == "integer":
            return int(value) if value is not None else 0
        elif datatype == "decimal":
            return float(value) if value is not None else 0.0
        elif datatype == "boolean":
            return bool(value) if value is not None else False
        elif datatype == "date" or datatype == "datetime":
            return datetime_parse(str(value), datatype) if value is not None else datetime.datetime.min
        else:
            return str(value).lower() if value is not None else ""

    while end >= 0:
        sort_by = valid_ordering[end]
        reverse = sort_by.startswith('-')
        if reverse:
            sort_by = sort_by[1:]
        sorted_entrylist_array = sorted(sorted_entrylist_array, key=lambda x: sort_key(x, sort_by), reverse=reverse)

        end -= 1
    return sorted_entrylist_array
    
        



def paginate_entry(entrylist_array, page, size, offset):
    runningOffset = offset
    runningSize = size
    entrylist_paginated = entrylist_array
    if page:
        entrylist_count = len(entrylist_array)
        entrylist_paginated = entrylist_array[offset:(offset + size)]
        if offset < entrylist_count:
            runningOffset = 0
        if (size + offset) < entrylist_count:
            runningSize = -1  
    return entrylist_paginated, runningOffset, runningSize
    

def list_entries(args, table):
    unfiltered = False
    page = None
    size = 10

    filter_type = "&"
    order_by = []

    # check for pagination
    if "page" in args:
        page = args.pop("page")
        if "size" in args:
            size = args.pop("size")

    # check for filter_type key

    if "filter_type" in args:
        filter_type = args.pop("filter_type")
        filter_type = filter_type if filter_type == "|" else "&"

    # check for order_by key
    if "order_by" in args:
        # can be comma separated
        # can contain "-" for reverse chronological order

        order_by = args.pop("order_by")
        order_by = order_by.split(",")

    offset = 0
    if page:
        try:
            page = int(page)
            page = page if page > 0 else 1
            size = int(size)
            offset = (page - 1) * size
        except:
            return {"error": "page and size must be integers"}
    
    try:

        entrylist_array, data_type_map = build_entry_array(table.entry_lists)

        filtered_entrylist = build_entry_filter(entrylist_array, data_type_map, args, filter_type)

        sorted_entrylist = build_entry_ordering(filtered_entrylist, data_type_map, order_by)

        paginated_entrylist, runningOffset, runningSize = paginate_entry(sorted_entrylist, page, size, offset)

    except Exception as e:
        print(e)
        return {"error": "Something went wrong"} 
    else:
        # return return_entry_data(page, size, offset, runningSize, runningOffset, data, list_cache_key, unfiltered)
        return return_entry_data(page, size, offset, runningSize, runningOffset, paginated_entrylist)






def create_null_value_entries(table, table_param):
    entrylists = table.entry_lists


    for entrylist in entrylists:
        e = Entry()
        table_param.entries.append(e)
        entrylist.entries.append(e)

def create_default_value_entries(table, table_param, default_value, is_fk=False):
    entrylists = table.entry_lists

    if is_fk:

        try:
            rel_id = table_param.foreign_key_reference_id
            relationship_stmt = db.select(Relationship)\
                .filter_by(foreign_key_rel_id = rel_id, entry_ref_pk = default_value, child_table_id=table_param.table_id)\
                .options(selectinload(Relationship.entrylists))
            relationship = db.session.scalar(relationship_stmt)
            if not relationship:
                relationship = Relationship(entry_ref_pk=default_value, foreign_key_rel_id=rel_id, child_table_id=table_param.table_id)
                db.session.add(relationship)
        except:
            raise Exception({"error": "Could not reference the foreign key id while getting/creating relationship"})

    for entrylist in entrylists:
        e = Entry(value = default_value)
        table_param.entries.append(e)
        entrylist.entries.append(e)
        if is_fk:
            if entrylist not in relationship.entrylists:
                relationship.entrylists.append(entrylist)
                db.session.add(relationship)


def update_default_value_entries(table_param, default_value, is_fk=False):
    #update the values that are null.. doesn't change previous values.
    entries = table_param.entries

    if is_fk:
        try:
            rel_id = table_param.foreign_key_reference_id
            relationship_stmt = db.select(Relationship)\
                .filter_by(foreign_key_rel_id = rel_id, entry_ref_pk = default_value, child_table_id=table_param.table_id)\
                .options(selectinload(Relationship.entrylists))
            relationship = db.session.scalar(relationship_stmt)
            if not relationship:
                relationship = Relationship(entry_ref_pk=default_value, foreign_key_rel_id=rel_id, child_table_id=table_param.table_id)
                db.session.add(relationship)
        except Exception as e:
            raise Exception({"error": "Could not reference the foreign key id while getting/creating relationship"})
    for entry in entries:
        if not entry.value:
            entry.value = default_value
            if is_fk:
                entrylist = entry.entry_list
                if entrylist not in relationship.entrylists:
                    relationship.entrylists.append(entrylist)
                    db.session.add(relationship)


# def update_default_value_entries(table_param, default_value, is_fk=False):
#     #update the values that are null.. doesn't change previous values.
#     entries = table_param.entries
#     for entry in entries:
#         if not entry.value:
#             entry.value = default_value
#             if is_fk:   
#                 try:
#                     rel_id = table_param.foreign_key_reference_table.table_reference.table_id
#                     relationship = Relationship.query.filter_by(foreign_key_rel_id = rel_id, entry_ref_pk = default_value, child_table_id=table_param.table_id).first() 
#                     if not relationship:
#                         relationship = Relationship(entry_ref_pk=default_value, foreign_key_rel_id=rel_id, child_table_id=table_param.table_id)
#                     if entrylist not in relationship.entrylists:
#                         relationship.entrylists.append(entrylist)
#                         db.session.add(relationship)
#                 except:
#                     raise Exception({"error": "Could not reference the foreign key id while getting/creating relationship"})










    
# def list_entries(args, table):
#     unfiltered = False
#     page = None
#     size = 10
#     if "page" in args:
#         page = args.pop("page")
#         if "size" in args:
#             size = args.pop("size")
    
#     data = []
#     try:
#         offset = 0
#         if page:
#             try:
#                 page = int(page)
#                 page = page if page > 0 else 1
#                 size = int(size)
#                 offset = (page - 1) * size
#             except:
#                 return {"error": "page and size must be integers"}

#         if args:
#             runningOffset = offset
#             runningSize = size
#             found_valid_arg = False # if params passed in are valid or not
#             # if runningOffset >  0:
#             get_entryLists = table.entry_lists
#             for entry_list in get_entryLists:
#                 entry_data = {}
#                 get_entries = entry_list.entries
#                 filter_in = True
#                 for entry in get_entries:
#                     tp_name = entry.tableparameter.name
#                     e_value = parse_value(entry.tableparameter, entry.value)

#                     if e_value is not None:
#                         found_valid_arg, filter_in = query_filter(tp_name, args, entry.tableparameter.data_type.name, entry.value, found_valid_arg, filter_in)
                        
#                     entry_data[tp_name] = e_value
#                 if filter_in:
#                     # We need to filter each entry before paginating.. 
#                     if page and runningOffset > 0:
#                         runningOffset -= 1
#                         continue
#                     if page and runningSize == 0:
#                         runningSize -= 1
#                         continue
#                     if page and runningSize < 0:
#                         break
#                     data.append(entry_data)
#                     if page:
#                         runningSize -= 1
#             if found_valid_arg:
#                 return return_entry_data(page, size, offset, runningSize, runningOffset, data, None)
#         data = []
#         runningOffset = offset
#         runningSize = size
#         unfiltered = True

#         # This needs to be revalidated
#         # print('got here')
#         # entrylists = get_raw_cache(list_cache_key)
#         # print(entrylists)
#         # if entrylists:
#         #     return entrylists
           
#         # if not page:
 
#         if page:
#             entrylist_count = len(table.entry_lists)
#             entrylist_list = table.entry_lists[offset:(offset + size)]
#             if offset < entrylist_count:
#                 runningOffset = 0
#             if (size + offset) < entrylist_count:
#                 runningSize = -1      
#         else:
#             entrylist_list = table.entry_lists

#         for entry_list in entrylist_list:
#             if entry_list.entries:
#                 data.append({entry.tableparameter.name: parse_value(entry.tableparameter, entry.value) for entry in entry_list.entries})

#     except Exception as e:
#         print(e)
#         return {"error": "Something went wrong"} 
#     else:
#         # return return_entry_data(page, size, offset, runningSize, runningOffset, data, list_cache_key, unfiltered)
#         return return_entry_data(page, size, offset, runningSize, runningOffset, data, unfiltered)

    
