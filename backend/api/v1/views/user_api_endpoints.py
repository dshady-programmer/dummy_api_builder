"""
Defining api routes specific to the user created
apis
"""

from api.v1.views import app_views
from flask import request
from .utils.response import format_response
from api.v1.auth.auth import login_required
from models.api import Api
from models.table import Table
from models import db
from .utils.validate import validate_name
from .utils.cache_utils import (
    get_cache, set_cache, 
    delete_cache, multiple_key_delete,
    user_cache_namespace, api_cache_namespace
)
from .utils.resource_delete_utils import delete_API
from sqlalchemy.orm import selectinload


@app_views.route('/my_apis')
@login_required
def my_api_list(user):
    # from models.tableparameter import parameter_constraints
    # s = db.delete(parameter_constraints).where(parameter_constraints.c.tableparameter_id.in_([7,8,9]))
    # db.session.execute(s)
    # db.session.commit()
    # from models import ForeignKeyFieldReferenceTable
    # s = db.delete(ForeignKeyFieldReferenceTable).where(ForeignKeyFieldReferenceTable.table_id.in_([4]))
    # db.session.execute(s)
    # db.session.commit()
    # print("foreign key scalar", db.session.execute(db.text("PRAGMA foreign_keys")).scalar())
    # key = f"{user_cache_namespace(user.id)}:apis"
    # cached_data = get_cache(key)

    # if cached_data is not None:
    #     return jsonify(cached_data), 200
    
    stmt = db.select(Api).filter_by(user_id=user.id)
    user_apis = db.session.scalars(stmt).all()

    apis = [
            {"id": api.id, "name": api.name, "description": api.description}
            for api in user_apis
        ]


    # set_cache(key, apis)
    return format_response(data=apis)


@app_views.route('/my_api/<api_id>')
@login_required
def my_api_detail(user, api_id):

    # key = f"{api_cache_namespace(user.id, api_id)}:detail"
    # cached_data = get_cache(key)
    # if cached_data is not None:
    #     return jsonify(cached_data), 200
    stmt = db.select(Api).filter_by(id=api_id, user_id=user.id).options(selectinload(Api.tables))
    api = db.session.scalar(stmt)
    if not api:
        return format_response(status="error", message="Api doesn't exist", code=404)
    tables = [
        {
            "id": table.id, 
            "name": table.name,
            "description": table.description,
        }
        for table in api.tables
    ]

    data = {
        "id": api.id, 
        "name": api.name,
        "description": api.description,
        "tables": tables
    }
    # set_cache(key, data)
    return format_response(data=data)




@app_views.route('/create_new_api', methods=["POST"])
@login_required
def create_new_api(user):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    if not name:
        return format_response(status="error", message="name of the api must be provided", code=400)
    stmt = db.select(db.exists().where(Api.name == name, Api.user_id == user.id))
    if db.session.scalar(stmt):
        return format_response(status="error", message="name with api already exists for this user", code=400)
    if not validate_name(name):
        return format_response(status="error", message="Api name must be a valid python identifier, not a keyword and must be atleast 3 letters", code=400)

    new_api = Api(name=name, description=description, user_id=user.id)
    db.session.add(new_api)
    # key = f"{user_cache_namespace(user.id)}:apis"
    # delete_cache(key)
    db.session.commit()
    return format_response(data={"id": new_api.id, "name": new_api.name, "desc": new_api.description})



@app_views.route('/update_api/<id>', methods=['PUT'])
@login_required
def update_api_info(user, id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    stmt = db.select(Api).filter_by(id=id, user_id=user.id)
    api = db.session.scalar(stmt)
    if not api:
        return format_response(status="error", message=f"api with id {id} doesn't exist", code=400)

    # add a check to update all relationships
    if name and validate_name(name):
        api.name = name
    if description:
        api.description = description
    # list_key = f"{user_cache_namespace(user.id)}:apis"
    # detail_key = f"{api_cache_namespace(user.id, api.id)}:detail"
    # multiple_key_delete([list_key, detail_key])
    db.session.commit()
    return format_response(data={"id": api.id, "name": api.name, "desc": api.description})


@app_views.route('/delete_api/<id>', methods=['DELETE'])
@login_required
def delete_api(user, id):
    stmt = db.select(Api).filter_by(id=id, user_id=user.id).options(selectinload(Api.tables).joinedload(Table.reference))
    api = db.session.scalar(stmt)
    if not api:
        return format_response(status="error", message=f"api with id {id} doesn't exist", code=400)
  

    # Safe check there's no foreign key + primary key reference before deletion
    status, msg, code = delete_API(db, api)

    if not status:
        return format_response(status="error", message=msg, code=code)

    # list_key = f"{user_cache_namespace(user.id)}:apis"
    # detail_key = f"{api_cache_namespace(user.id, api.id)}:detail"
    # multiple_key_delete([list_key, detail_key])
    return format_response(code=204)
