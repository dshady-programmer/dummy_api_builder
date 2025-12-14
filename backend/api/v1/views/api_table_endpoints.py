"""
Defining routes for performing crud operations on
tables/model in an api
"""

from api.v1.views import app_views
from flask import request, jsonify
from api.v1.auth.auth import login_required
from models import db, Api, Table
from .utils.validate import validate_name
from .utils.model_utils import parse_and_create_tableparameters, parse_and_update_tableparameters



"""
We won't be implementing a table/model list endpoint
as it would have been added with api_list
"""


@app_views.route('/my_api/<api_id>/create_model', methods=["POST"])
@login_required
def create_model(user, api_id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    table_parameters = data.get('tbl_params') or []
    # Atleast one table parameter is required
    # Tableparameter refers to the model fields (like name = string() etc..)
    # table_parameters would contain a list of dictionaries defining the attribute for the model
    if type(table_parameters) != list and not len(table_parameters):
        return jsonify({"error": "table parameters are required"}), 400
    
    if not name:
        return jsonify({"error": "name of the model is required"}), 400

    api = Api.query.filter_by(id=api_id, user_id=user.id).first()
    if not api:
        return jsonify({"error": "no api of such is associated to the user"}), 400
    
    get_table = Table.query.filter_by(api_id=api_id, name=name).first()
    if get_table:
        return jsonify({"error": "Table already exists"}), 400
    
    if not validate_name(name):
        return jsonify({"error": "Table name must be a valid python identifier, not a python keyword and must be atleast 3 letters"}), 400
    new_table = Table(name=name, description=description, api_id=api_id)
    db.session.add(new_table)
    response = parse_and_create_tableparameters(table_parameters, new_table, user)
    if 'error' in response:
        return jsonify(response), 400
    return jsonify(response), 200



@app_views.route('/my_api/<api_id>/update_model/<model_name>', methods=["PUT"])
@login_required
def update_model(user, api_id, model_name):
    """
    The current update model functionality is somewhat 
    rigid and would be improved
    
    """
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    table_parameters = data.get('tbl_params') or []
    api = Api.query.filter_by(id=api_id, user_id=user.id).first()
    entry_present = False
    if not api:
        return jsonify({"error": "no api of such is associated to the user"}), 400
    get_table = Table.query.filter_by(name=model_name, api_id=api_id).first()
    if not get_table:
        return jsonify({"error": "Table doesn't exist"}), 400
    if get_table.entry_lists:
        entry_present = True
    if type(table_parameters) != list:
        return jsonify({"error": "table_parameter must be a list"}), 400
    if name and validate_name(name):
        get_table.name = name

    if description:
        get_table.description = description
 
    response = parse_and_update_tableparameters(table_parameters, get_table, user, entry_present)
    if 'error' in response:
        return jsonify(response), 400
    return jsonify(response), 200


@app_views.route('/my_api/<api_id>/show_model/<model_name>', methods=["GET"])
@login_required
def show_model(user, api_id, model_name):
    api = Api.query.filter_by(id=api_id, user_id=user.id).first()
    if not api:
        return jsonify({"error": "no api of such is associated to the user"}),400
    get_table = Table.query.filter_by(name=model_name, api_id=api_id).first()
    if not get_table:
        return jsonify({"error": "Table doesn't exist"}), 400
    tbl_params = []
    for params in get_table.table_parameters:
        tbl_constraints = []
        for const in params.constraints:
            tbl_constraints.append(const.name.value)
        foreign_key_ref = None
        ref_table = params.foreign_key_reference_table
        if ref_table:
            foreign_key_ref = f"{ref_table.table_reference.api.name}.{ref_table.table_reference.name}"
        tbl_params.append({
            "index": params.id,
            "name": params.name,
            "datatype": params.data_type.name,
            "dt_length": params.dataType_length,
            "default_value": params.default_value, 
            "foreign_key_rf": foreign_key_ref,
            "constraints": tbl_constraints
        })
    
    return jsonify({
        "id": get_table.id, 
        "name": get_table.name,
        "desc": get_table.description,
        "table_params": tbl_params
        })



@app_views.route('/my_api/<api_id>/delete_model/<model_name>', methods=["DELETE"])
@login_required
def delete_model(user, api_id, model_name):
    api = Api.query.filter_by(id=api_id, user_id=user.id).first()
    if not api:
        return jsonify({"error": "no api of such is associated to the user"}),400
    t = Table.query.filter_by(name=model_name, api_id=api_id).first()
    tbl_ps = t.table_parameters
    for tp in tbl_ps:
        tp.constraints.clear()
    db.session.delete(t.reference)
    db.session.delete(t)

    db.session.commit()
    
    return jsonify(''), 204