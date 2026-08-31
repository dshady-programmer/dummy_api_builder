"""
Defining routes for performing crud operations on
tables/model in an api
"""

from api.v1.views import app_views
from flask import request
from .utils.response import format_response
from api.v1.auth.auth import login_required
from models import db, Api, Table, TableParameter, Entry, EntryList, Relationship
from .utils.validate import validate_name
from .utils.model_utils import (
    parse_and_create_tableparameters, 
    parse_and_update_tableparameters
)
from .utils.resource_delete_utils import delete_table, delete_entrylists

from sqlalchemy.orm import selectinload, joinedload
from .utils.cache_utils import (
    get_cache, set_cache, delete_cache, 
    api_cache_namespace, multiple_key_delete

)


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
    if type(table_parameters) != list or not len(table_parameters):
        return format_response(status="error", message="table parameters are required", code=400)
    if not name:
        return format_response(status="error", message="name of the model is required", code=400)

    api_stmt = db.select(db.exists().where(Api.id == api_id, Api.user_id == user.id))
    api = db.session.scalar(api_stmt)
    if not api:
        return format_response(status="error", message="no api of such is associated with the user", code=400)

    table_stmt = db.select(db.exists().where(Table.api_id == api_id, Table.name == name))
    table = db.session.scalar(table_stmt)
    if table:
        return format_response(status="error", message="Table already exists", code=400)
    
    if not validate_name(name):
        return format_response(status="error", message="Table name must be a valid python identifier, not a python keyword and must be atleast 3 letters", code=400)
    new_table = Table(name=name, description=description, api_id=api_id)
    db.session.add(new_table)
    try:
        response = parse_and_create_tableparameters(table_parameters, new_table, user)
        if 'error' in response:
            return format_response(status="error", message=response['error'], code=400)


        return format_response(data=response, code=201)
    except Exception as e:
        print(e)
        return format_response(status="error", message="Database Integrity Error", code=409)



@app_views.route('/my_api/<api_id>/update_model/<model_id>', methods=["PUT"])
@login_required
def update_model(user, api_id, model_id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    table_parameters = data.get('tbl_params') or []

    api_stmt = db.select(db.exists().where(Api.id == api_id, Api.user_id == user.id))
    api = db.session.scalar(api_stmt)
    entry_present = False
    # should_invalidate_api_detail = False
    if not api:
        return format_response(status="error", message="no api of such is associated with the user", code=400)

    table_stmt = db.select(Table).filter_by(id=model_id, api_id=api_id)\
                                                .options(selectinload(Table.table_parameters)\
                                                .selectinload(TableParameter.constraints),
                                                selectinload(Table.table_parameters)\
                                                .joinedload(TableParameter.foreign_key_reference_table),
                                                selectinload(Table.table_parameters).selectinload(TableParameter.entries)\
                                                    .joinedload(Entry.entry_list)

                                                ).with_for_update()
    table = db.session.scalar(table_stmt)

    if not table:
        return format_response(status="error", message="Table doesn't exist", code=400)

    entry_count = db.session.scalar(
            db.select(db.func.count())
            .select_from(EntryList)
            .where(EntryList.table_id == table.id)
        )
    if entry_count:
        entry_present = True
    if type(table_parameters) != list:
        return format_response(status="error", message="table_parameter must be a list", code=400)
    if name and validate_name(name) and table.name != name:
        table.name = name
        # should_invalidate_api_detail = True

    if description and table.description != description:
        table.description = description
        # should_invalidate_api_detail = True

    try:
        response = parse_and_update_tableparameters(table_parameters, table, user, entry_present)
        if 'error' in response:
            return format_response(status="error", message=response['error'], code=400)

        # table_cache_key = f"{api_cache_namespace(user.id, api_id)}:model:{table.id}"
        # if should_invalidate_api_detail:
        #     api_cache_key = f"{api_cache_namespace(user.id, api_id)}:detail"
        #     multiple_key_delete([table_cache_key, api_cache_key])
        # else:
        #     delete_cache(table_cache_key)

        return format_response(data=response)
        
    except Exception as e:
        print(e)
        return format_response(status="error", message="Database Integrity Error", code=409)




@app_views.route('/my_api/<api_id>/show_model/<model_id>', methods=["GET"])
@login_required
def show_model(user, api_id, model_id):
    # key = f"{api_cache_namespace(user.id, api_id)}:model:{model_id}"
    # no_of_entries_key = f"{api_cache_namespace(user.id, api_id)}:model:{model_id}:num_of_entries"
    # cache_num_of_entries = get_cache(no_of_entries_key)
    # cached_data = get_cache(key)
    # if cached_data is not None:
    #     if cache_num_of_entries is not None and cache_num_of_entries != cached_data["number_of_entries"]:
    #         cached_data['number_of_entries'] = cache_num_of_entries
    #     return jsonify(cached_data), 200
    api_stmt = db.select(db.exists().where(Api.id == api_id, Api.user_id == user.id))
    api = db.session.scalar(api_stmt)
    if not api:
        return format_response(status="error", message="no api of such is associated with the user", code=404) 
    table_stmt = db.select(Table).filter_by(id=model_id, api_id=api_id)\
                                            .options(selectinload(Table.table_parameters)\
                                            .selectinload(TableParameter.constraints))
    table = db.session.scalar(table_stmt)
    if not table:
        return format_response(status="error", message="Table doesn't exist", code=404) 
    tbl_params = []
    
    for param in table.table_parameters:
        tbl_constraints = [const.name.value for const in param.constraints]
        foreign_key_ref = None
        ref_table = param.foreign_key_reference_table
        if ref_table:
            foreign_key_ref = f"{ref_table.table_reference.api.name}.{ref_table.table_reference.name}"
        tbl_params.append({
            "index": param.id,
            "name": param.name,
            "datatype": param.data_type.name,
            "dt_length": param.dataType_length,
            "default_value": param.default_value, 
            "foreign_key_rf": foreign_key_ref,
            "constraints": tbl_constraints
        })
    num_of_entries = db.session.scalar(
            db.select(db.func.count())
            .select_from(EntryList)
            .where(EntryList.table_id == table.id)
        )
    data = {
        "id": table.id, 
        "name": table.name,
        "api_name": api.name,
        "number_of_entries": num_of_entries,
        "desc": table.description,
        "table_params": tbl_params
        }
    # set_cache(no_of_entries_key, num_of_entries)
    # set_cache(key, data)
    return format_response(data=data)



@app_views.route('/my_api/<api_id>/delete_model/<model_id>', methods=["DELETE"])
@login_required
def delete_model(user, api_id, model_id):
    api_stmt = db.select(db.exists().where(Api.id == api_id, Api.user_id == user.id))
    api = db.session.scalar(api_stmt)
    if not api:
        return format_response(status="error", message="no api of such is associated with the user", code=404)

    table_stmt = db.select(Table).filter_by(id=model_id, api_id=api_id).options(joinedload(Table.reference))
    t = db.session.scalar(table_stmt)
    if not t:
        return format_response(status="error", message= "Table doesn't exist", code=404)


    # delete table but with a check on relationships
    status, msg, code = delete_table(db, t)
    if not status:
        return format_response(status="error", message=msg, code=code)

    
    # table_cache_key = f"{api_cache_namespace(user.id, api_id)}:model:{t.id}"
    # num_entries = f"{api_cache_namespace(user.id, api_id)}:model:{t.id}:num_of_entries"
    # api_cache_key = f"{api_cache_namespace(user.id, api_id)}:detail"
    # multiple_key_delete([table_cache_key, num_entries, api_cache_key])
   
    return format_response(code=code)



 
@app_views.route('/my_api/<api_id>/truncate_model/<model_id>', methods=["DELETE"])
@login_required
def truncate_model(user, api_id, model_id):
    from models.relationship import entrylist_relationships
    api_stmt = db.select(db.exists().where(Api.id == api_id, Api.user_id == user.id))
    api = db.session.scalar(api_stmt)
    if not api:
        return format_response(status="error", message="no api of such is associated with the user", code=404)
  
    table_stmt = db.select(Table).filter_by(id=model_id, api_id=api_id).options(joinedload(Table.reference))
    t = db.session.scalar(table_stmt)
    if not t:
        return format_response(status="error", message="Table doesn't exist", code=400)

    entrylist_stmt = db.select(EntryList).filter_by(table_id=t.id)
    entrylists = db.session.scalars(entrylist_stmt).all()

    status, msg, code = delete_entrylists(db, t.reference.id, entrylists)

    if status:
        # num_entries = f"{api_cache_namespace(user.id, api_id)}:model:{model_id}:num_of_entries"
        # set_cache(num_entries, 0)
        return format_response(code=code)
    else:
        return format_response(status="error", message=msg, code=code)


