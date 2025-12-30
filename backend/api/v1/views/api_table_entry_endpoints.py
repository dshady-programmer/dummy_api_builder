"""
Creating entries in the table:
e.g name="peter"
age=12
etc..
"""
from api.v1.views import app_views
from flask import request, jsonify, make_response
from models import (
    Api,
    Table,
    User,
    Entry,
    EntryList,
    Relationship,
    ForeignKeyFieldReferenceTable, db
)

from .utils.model_entry_utils import (
    create_entry, 
    list_entries, 
    update_entry
) 

from .utils.cache_utils import (
    get_cache,
    set_cache,
    set_user_api_cache,
    invalidate_user_cache_api,
    

)
from .utils.validate import retrieve_remaining_rows_limit
from .utils.parsers import parse_value, csv_file_parser


@app_views.route('<api_token>/my_api/<api_name>/model/<model_name>', methods=["GET", "POST"])
def add_list_entry(api_token, api_name, model_name):
    user = User.query.filter_by(api_token=api_token).first()
    if not user:
        return make_response("invalid token", 401)

    api = Api.query.filter_by(name=api_name, user_id=user.id).first()
    if not api:
        return make_response(f"{api_name} does not exists in the users catalog", 400)
    table = Table.query.filter_by(name=model_name, api_id=api.id).first()
    if not table:
        return make_response(f"model {model_name} doesn't exist in the api", 400)
    list_cache_key_format = "{api_token}-{api_name}-{model_name}-entries"
    list_cache_key = list_cache_key_format.format(api_token=api_token, api_name=api_name, model_name=model_name)
    if request.method == "POST":
        remaining_rows = retrieve_remaining_rows_limit(user)
        if remaining_rows <= 0:
            return make_response("You have reached your maximum number of rows allowed.", 403)

        csv_file = request.files.get("csv_file")
        if csv_file:
            delimiter = request.form.get("delimiter") or ","
            entries, error = csv_file_parser(csv_file, table=table, remaining_rows=remaining_rows, delimiter=delimiter)
            if error:
                return jsonify({"error": error}), 400
        else:
            data = request.get_json()
            entries = data.get("entries")
        
        if type(entries) not in [list, dict]: 
            return jsonify({"error": "Entries must be an object or a an array of objects"}), 400
        no_of_entries_key = f"{user.id}:{api.id}:{model_name}:num_of_entries"
        prev_num = get_cache(no_of_entries_key)


        if type(entries) == dict:
            response = create_entry(table, entries)
            if 'error' in response:
                return jsonify(response), 400
            if prev_num is not None:
                set_cache(no_of_entries_key, prev_num + 1)
            return jsonify(response), 200
        else:
            responses = []
            if len(entries) > remaining_rows:
                entries = entries[:remaining_rows]
            for entry in entries:
                response = create_entry(table, entry)

                if 'error' in response:
                    num_of_responses = len(responses)
                    stringified_key_entry = {str(k): v for k, v in entry.items()}
                    if prev_num is not None:
                        set_cache(no_of_entries_key, prev_num + num_of_responses)
                    return jsonify({
                            "status": "error",
                            "error": {
                                "entry": stringified_key_entry,
                                "response": response
                            },
                            "successful_entries": responses,
                            "Number of entries added": num_of_responses
                        }), 400
                responses.append(response)
            num_of_responses = len(responses)
            if prev_num is not None:
                set_cache(no_of_entries_key, prev_num + num_of_responses)    
            return jsonify({
                "status": "success",
                "results": responses,
                "Number of entries added": num_of_responses
            }), 200

                
    elif request.method == "GET":
        args = dict(request.args)
        response = list_entries(args, table, list_cache_key)
        if type(response) == dict and "error" in response:
            
            return jsonify(response), 400
        return jsonify(response), 200



@app_views.route('<api_token>/my_api/<api_name>/model/<model_name>/<model_id>', methods=["PUT", "GET", "DELETE"])
def update_delete_retrieve_entry(api_token, api_name, model_name, model_id):

    user = User.query.filter_by(api_token=api_token).first()
    if not user:
        return make_response("invalid api id", 401)
    
    cache_key_format = "{api_token}-{api_name}-{model_name}-{model_id}"
    cache_key = cache_key_format.format(api_token=api_token, api_name=api_name, model_name=model_name, model_id=model_id)
    api = Api.query.filter_by(name=api_name, user_id=user.id).first()
    if not api:
        return make_response(f"{api_name} does not exists in the users catalog", 400)
    table = Table.query.filter_by(name=model_name, api_id=api.id).first()
    if not table:
        return make_response(f"model {model_name} doesn't exist in the api", 400)


    e_list = EntryList.query.filter_by(table_id = table.id, primary_key_value = model_id).first()
    if not e_list:
            return jsonify({"error": "primary key value doesn't match any"}), 400
    child_tables = []
    
    
    fk_ref_table = table.reference # to grab reference tables incase of foreign key relationships 
    
    if request.method == "PUT":
        data = request.get_json()
        entries = data.get("entries") or {}
        if type(entries) != dict:
            return jsonify({"error": "Entries must be an object"}), 400

        response = update_entry(entries, table, e_list)
        if "error" in response:
            return jsonify(response), 400         
        rels = Relationship.query.filter_by(entry_ref_pk=e_list.primary_key_value, foreign_key_rel_id=fk_ref_table.id)
        for r in rels:
            child_tables.append(r.child_table)   
        invalidate_user_cache_api(cache_key, api.id, table.name, child_tables)
        return jsonify(response), 200
    


    if request.method == "DELETE":
        entries = Entry.query.filter_by(entry_list_id=e_list.id).delete()
        rels = Relationship.query.filter_by(entry_ref_pk=e_list.primary_key_value, foreign_key_rel_id=fk_ref_table.id)
        for r in rels:
            child_tables.append(r.child_table)
            r.entrylists.clear()
            db.session.delete(r)
        EntryList.query.filter_by(table_id = table.id, primary_key_value = model_id).delete()
        db.session.commit()
        invalidate_user_cache_api(cache_key, api.id, table.name, child_tables)
        return jsonify({'message': 'Entry succesfully deleted'}), 204 # NO content afterall


    if request.method == "GET":
        cached_data = get_cache(cache_key)
        if cached_data is not None:
            # print(cached_data)
            return jsonify(cached_data)
        data = {}
        for data_entry in e_list.entries:
            fieldName = data_entry.tableparameter.name
            data[fieldName] = parse_value(data_entry.tableparameter, data_entry.value)
        # rel_key = db.session(Relationship).filter(Relationship.fk_rel.like(f"{tableKeyName}%"), Relationship.entry_ref_pk=e_list.primary_key_value).first()
        rels = Relationship.query.filter_by(entry_ref_pk=e_list.primary_key_value, foreign_key_rel_id=fk_ref_table.id)
        rel_key_data = {} # format {"posts":[..]}
    

        
        for rel in rels:
            child_tables.append(rel.child_table)
            fk_rel_name = f"{rel.child_table.api.name.lower()}_{rel.child_table.name.lower()}s"
            rel_key_data[fk_rel_name] = []
            for e_list_rel in rel.entrylists:
                rel_data = {}
                for ent in e_list_rel.entries:
                    rel_data[ent.tableparameter.name] = parse_value(ent.tableparameter, ent.value)
                rel_key_data[fk_rel_name].append(rel_data) # <api_name>_<model_name>s
        data["relationships"] = rel_key_data

        set_user_api_cache(cache_key, data, api.id, table.name, child_tables)
        return jsonify(data), 200
