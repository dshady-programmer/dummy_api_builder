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

from .utils.parsers import parse_value


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
    if request.method == "POST":
        data = request.get_json()
        entries = data.get("entries")
        if type(entries) not in [list, dict]: 
            return jsonify({"error": "Entries must be an object or a an array of objects"}), 400
        # This logic would be refactored. 
        if type(entries) == dict:
            response = create_entry(table, entries)
            if 'error' in response:
                return jsonify(response), 400
            return jsonify(response), 200
        else:
            responses = []
            for entry in entries:
                response = create_entry(table, entry)
                if 'error' in response:
                    return jsonify({
                            "status": "error",
                            "error": {
                                "entry": entry,
                                "response": response
                            },
                            "successful_entries": responses
                        }), 400
                responses.append(response)
                
            return jsonify({
                "status": "success",
                "results": responses
            }), 200

                
    elif request.method == "GET":
        args = dict(request.args)
        response = list_entries(args, table)
        if type(response) == dict and "error" in response:
            return jsonify(response), 400
        return jsonify(response), 200



@app_views.route('<api_token>/my_api/<api_name>/model/<model_name>/<model_id>', methods=["PUT", "GET", "DELETE"])
def update_delete_retrieve_entry(api_token, api_name, model_name, model_id):
    user = User.query.filter_by(api_token=api_token).first()
    if not user:
        return make_response("invalid api id", 401)
    api = Api.query.filter_by(name=api_name, user_id=user.id).first()
    if not api:
        return make_response(f"{api_name} does not exists in the users catalog", 400)
    table = Table.query.filter_by(name=model_name, api_id=api.id).first()
    if not table:
        return make_response(f"model {model_name} doesn't exist in the api", 400)
    e_list = EntryList.query.filter_by(table_id = table.id, primary_key_value = model_id).first()
    if not e_list:
            return jsonify({"error": "primary key value doesn't match any"}), 400
   
   
    if request.method == "PUT":
        data = request.get_json()
        entries = data.get("entries") or {}
        if type(entries) != dict:
            return jsonify({"error": "Entries must be an object"}), 400

        response = update_entry(entries, table, e_list)
        if "error" in response:
            return jsonify(response), 400            
        return jsonify(response), 200
    


    fk_ref_table = ForeignKeyFieldReferenceTable.query.filter_by(table_id=table.id).first() # to grab reference tables incase of foreign key relationships 
    if request.method == "DELETE":
        entries = Entry.query.filter_by(entry_list_id=e_list.id).delete()
        rels = Relationship.query.filter_by(entry_ref_pk=e_list.primary_key_value, foreign_key_rel_id=fk_ref_table.id)
        for r in rels:
            r.entrylists.clear()
            db.session.delete(r)
        EntryList.query.filter_by(table_id = table.id, primary_key_value = model_id).delete()
        db.session.commit()
        return jsonify({'message': 'Entry succesfully deleted'}), 204 # NO content afterall


    if request.method == "GET":
        data = {}
        for data_entry in e_list.entries:
            fieldName = data_entry.tableparameter.name
            data[fieldName] = parse_value(data_entry.tableparameter, data_entry.value)
        # rel_key = db.session(Relationship).filter(Relationship.fk_rel.like(f"{tableKeyName}%"), Relationship.entry_ref_pk=e_list.primary_key_value).first()
        rels = Relationship.query.filter_by(entry_ref_pk=e_list.primary_key_value, foreign_key_rel_id=fk_ref_table.id)
        rel_key_data = {} # format {"posts":[..]}
    

        for rel in rels:
            fk_rel_name = f"{rel.child_table.api.name.lower()}_{rel.child_table.name.lower()}s"
            rel_key_data[fk_rel_name] = []
            for e_list_rel in rel.entrylists:
                rel_data = {}
                for ent in e_list_rel.entries:
                    rel_data[ent.tableparameter.name] = parse_value(ent.tableparameter, ent.value)
                rel_key_data[fk_rel_name].append(rel_data) # <api_name>_<model_name>s
        data["relationships"] = rel_key_data
        return jsonify(data), 200
