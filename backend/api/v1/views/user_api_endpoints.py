"""
Defining api routes specific to the user created
apis
"""

from api.v1.views import app_views
from flask import request, jsonify
from api.v1.auth.auth import login_required
from models.api import Api
from models.table import Table
from models import db
from .utils.validate import validate_name



@app_views.route('/my_apis')
@login_required
def my_api_list(user):
    user_apis = user.user_apis
    apis = []
    for api in user_apis:
        # tables = []
        # for table in api.tables:
        #     tables.append({"id": table.id, 
        #                    "name": table.name,
        #                     "description": table.description,
        #                     })
        apis.append({
            "id": api.id, 
            "name": api.name,
            "description": api.description,
            # "tables": tables
            })
    return jsonify(apis)


@app_views.route('/my_api/<api_id>')
@login_required
def my_api_detail(user, api_id):
    api = Api.query.filter_by(id=api_id, user_id=user.id).first()
    if not api:
        return jsonify({"error": "Api doesn't exist"}), 400
    tables = []
    for table in api.tables:
        tables.append({"id": table.id, 
                        "name": table.name,
                        "description": table.description,
                        })
    return jsonify({
        "id": api.id, 
        "name": api.name,
        "description": api.description,
        "tables": tables
    })




@app_views.route('/create_new_api', methods=["POST"])
@login_required
def create_new_api(user):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    if not name:
        return jsonify({"error": "name of the api must be provided"}), 400
    if Api.query.filter_by(name=name, user_id = user.id).first():
        return jsonify({"error": "name with api already exists for this user"}), 400
    if not validate_name(name):
        return jsonify({"error": "Api name must be a valid python identifier, not a keyword and must be atleast 3 letters"}), 400
    new_api = Api(name=name, description=description, user_id=user.id)
    db.session.add(new_api)
    db.session.commit()
    return jsonify({"id": new_api.id, "name": new_api.name, "desc": new_api.description})



@app_views.route('/update_api/<id>', methods=['PUT'])
@login_required
def update_api_info(user, id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    api = Api.query.filter_by(id=id, user_id=user.id).first()
    if not api:
        return jsonify({"error": f"api with id {id} doesn't exist"}), 400

# add a check to update all relationships
    if name and validate_name(name):
        api.name = name
    if description:
        api.description = description
    db.session.commit()
    return jsonify({"id": api.id, "name": api.name, "desc": api.description})


@app_views.route('/delete_api/<id>', methods=['DELETE'])
@login_required
def delete_api(user, id):
    api = Api.query.filter_by(id=id, user_id=user.id).first()
    if not api:
        return jsonify({"error": "api doesn't exist"}), 400
    # Table.query.filter_by(api_id=api.first().id).delete()
    db.session.delete(api)
    db.session.commit()
    return jsonify(''), 204
