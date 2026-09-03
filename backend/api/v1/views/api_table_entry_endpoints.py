"""
Creating entries in the table:
e.g name="peter"
age=12
etc..
"""
from sqlalchemy.orm import selectinload, joinedload
from api.v1.views import app_views
from flask import request
from models import (
    Api,
    Table,
    TableParameter,
    User,
    Entry,
    EntryList,
    Relationship,
    UserLimit, db
)
from models.user import MAX_ROW_FOR_USER
from executor import init_executor
from .utils.resource_delete_utils import delete_entrylists
from .utils.response import format_response
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
    update_entry_list_cache_on_add_new_entries
    

)
from .utils.parsers import parse_value, csv_file_parser


@app_views.route('<api_token>/my_api/<api_name>/model/<model_name>', methods=["GET", "POST"])
def add_list_entry(api_token, api_name, model_name):
    user_stmt = db.select(User).filter_by(api_token=api_token)
    user = db.session.scalar(user_stmt)
    if not user:
        return format_response(status="error", message="invalid token", code=401)


    api_stmt = db.select(Api).filter_by(name=api_name, user_id=user.id)
    api = db.session.scalar(api_stmt)
    if not api:
        return format_response(status="error", message=f"{api_name} does not exists in the users catalog", code =400)
    table_stmt_post = db.select(Table).filter_by(name=model_name, api_id=api.id)\
        .options(selectinload(Table.table_parameters).selectinload(TableParameter.constraints),
                 selectinload(Table.table_parameters).joinedload(TableParameter.foreign_key_reference_table)\
                                                    .joinedload(TableParameter.foreign_key_default_value))\
        .with_for_update()

    table_stmt_get = db.select(Table).filter_by(name=model_name, api_id=api.id)\
            .options(selectinload(Table.entry_lists).selectinload(EntryList.entries)\
                     .joinedload(Entry.tableparameter))
    table_stmt = table_stmt_post if request.method == 'POST' else table_stmt_get
    table = db.session.scalar(table_stmt)
    if not table:
        return format_response(status="error", message=f"model {model_name} doesn't exist in the api", code=400)

    # list_cache_key_format = "{api_token}-{api_name}-{model_name}-entries"
    # list_cache_key = list_cache_key_format.format(api_token=api_token, api_name=api_name, model_name=model_name)
    if request.method == "POST":
        # remaining_rows = retrieve_remaining_rows_limit(user)
        
        user_limit = db.session.scalar(
            db.select(UserLimit).where(
                UserLimit.user_id == user.id
            ).with_for_update()
        )
        remaining_rows = MAX_ROW_FOR_USER - user_limit.current_rows
        if remaining_rows <= 0:
            db.session.rollback() # release the row
            return format_response(status="error", message="You have reached your maximum number of rows allowed", code=403)

        csv_file = request.files.get("csv_file")
        if csv_file:
            delimiter = request.form.get("delimiter") or ","
            entries, error = csv_file_parser(csv_file, table=table, remaining_rows=remaining_rows, delimiter=delimiter)
            if error:
                db.session.rollback()
                return format_response(status="error", message=error, code=400)
        else:
            data = request.get_json()
            entries = data.get("entries")
        
        if type(entries) not in [list, dict]:
            db.session.rollback() 
            return format_response(status="error", message="Entries must be an object or an array of objects", code=400)
        # no_of_entries_key = f"{user.id}:{api.id}:{model_name}:num_of_entries"
        # executor_thread = init_executor()
        # print("executor_thread", executor_thread)

        tracked_pks = set()
        tracked_unique_values = {}
        tracked_fk_values = {"relationships": {}, "values": {}}

        cached_required_parameters = []
        cached_parameters = {}
        cached_primary_key_fields = set()
        cached_default_pk_fields = {}
        if type(entries) == dict:
            response = create_entry(
                        table, entries, 
                        tracked_pks, 
                        tracked_unique_values,
                        tracked_fk_values, 
                        [], {}, set(), {}
                    )
            
            if 'error' in response:
                db.session.rollback()
                return format_response(status="error", message=response["error"], code=400)
            user_limit.current_rows += 1
            db.session.commit()
            # set_cache(no_of_entries_key, row.current_rows)
            # executor_thread.submit(update_entry_list_cache_on_add_new_entries, list_cache_key, [response])
            return format_response(data=response), 201
        else:
            responses = []
            errors = []
            if len(entries) > remaining_rows:
                entries = entries[:remaining_rows]
            for entry in entries:
                response = create_entry(
                    table, entry, tracked_pks, tracked_unique_values,
                    tracked_fk_values,
                    cached_required_parameters, cached_parameters,
                    cached_primary_key_fields, cached_default_pk_fields
                )

                if 'error' in response:
                    stringified_key_entry = {str(k): v for k, v in entry.items()}
                    error_detail = {
                                "entry": stringified_key_entry,
                                "response": response
                            }
                    errors.append(error_detail)
                    # set_cache(no_of_entries_key, row.current_rows)
                    # executor_thread.submit(update_entry_list_cache_on_add_new_entries, list_cache_key, responses)
                else:
                    responses.append(response)


            num_of_responses = len(responses)
            num_of_errors = len(errors)
            # if row is not None:
            #     set_cache(no_of_entries_key, row.current_rows) 
            try:
                successful_entries = num_of_responses - num_of_errors
                user_limit.current_rows += successful_entries
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return format_response(status="error", message="Database Integrity Error", code=409)

            if num_of_errors:
                return format_response(data={
                    "Number of errors": num_of_errors,
                    "errors": errors,
                    "successful_entries": responses,
                    "Number of entries added": num_of_responses
                })
            # executor_thread.submit(update_entry_list_cache_on_add_new_entries, list_cache_key, responses)   
            return format_response(data={
                "results": responses,
                "Number of entries added": num_of_responses
            })

                
    elif request.method == "GET":
        args = dict(request.args)
        # response = list_entries(args, table, list_cache_key)
        try:
            response = list_entries(args, table)
            if type(response) == dict and "error" in response:
                
                return format_response(status="error", message=response["error"], code=400)
            return format_response(data=response)
        except Exception as e:
            return format_response(status="error", message="Internal error", code=500)



@app_views.route('<api_token>/my_api/<api_name>/model/<model_name>/<model_id>', methods=["PUT", "GET", "DELETE"])
def update_delete_retrieve_entry(api_token, api_name, model_name, model_id):

    user_stmt = db.select(User).filter_by(api_token=api_token)
    user = db.session.scalar(user_stmt)
    if not user:
        return format_response(status="error", message="Invalid api id", code=401)
    
    # cache_key_format = "{api_token}-{api_name}-{model_name}-{model_id}"
    # cache_key = cache_key_format.format(api_token=api_token, api_name=api_name, model_name=model_name, model_id=model_id)
    api_stmt = db.select(Api).filter_by(name=api_name, user_id=user.id)
    api = db.session.scalar(api_stmt)
    if not api:
        return format_response(status="error", message=f"{api_name} does not exist in the user's catalog", code=400)
    
    table_stmt_put = db.select(Table).filter_by(name=model_name, api_id=api.id)\
        .options(joinedload(Table.reference),
                selectinload(Table.table_parameters).selectinload(TableParameter.constraints),
                 selectinload(Table.table_parameters).joinedload(TableParameter.foreign_key_reference_table))\
        .with_for_update()

    table_stmt_default = db.select(Table).filter_by(name=model_name, api_id=api.id)\
                        .options(joinedload(Table.reference))

    table_stmt = table_stmt_put if request.method == "PUT" else table_stmt_default
    table = db.session.scalar(table_stmt)
    if not table:
        return format_response(status="error", message=f"model {model_name} doesn't exist in the api", code=400)

    e_list_stmt = db.select(EntryList)\
        .filter_by(table_id=table.id, primary_key_value = model_id)\
        .options(selectinload(EntryList.entries))
    e_list_stmt = e_list_stmt.with_for_update() if request.method == 'PUT' else e_list_stmt
    e_list = db.session.scalar(e_list_stmt)
    if not e_list:
            return format_response(status="error", message="primary key value doesn't match any", code=400)
    # child_tables = []
    
    
    fk_ref_table = table.reference # to grab reference tables incase of foreign key relationships 
    
    if request.method == "PUT":
        data = request.get_json()
        entries = data.get("entries") or {}
        if type(entries) != dict:
            return format_response(status="error", message="Entries must be an object", code=400)

        try:

            response = update_entry(entries, table, e_list)
            if "error" in response:
                return format_response(status="error", message=response["error"], code=400)
            # rels = Relationship.query.filter_by(entry_ref_pk=e_list.primary_key_value, foreign_key_rel_id=fk_ref_table.id)
            # for r in rels:
            #     child_tables.append(r.child_table)   
            # invalidate_user_cache_api(cache_key, api.id, table.name, child_tables)
            return format_response(data=response)
        except Exception as e:
            return format_response(status="error", message="Database Integrity Error", code=409)

        


    if request.method == "DELETE":
        status, msg, code = delete_entrylists(db, fk_ref_table.id, [e_list])
        if status:
            return format_response(code=code, message="Entry succesfully deleted")

        else:
            return format_response(status="error", message=msg, code=code)

    if request.method == "GET":
        # cached_data = get_cache(cache_key)
        # if cached_data is not None:
        #     # print(cached_data)
        #     return jsonify(cached_data)
        try:
            data = {}
            for data_entry in e_list.entries:
                fieldName = data_entry.tableparameter.name
                data[fieldName] = parse_value(data_entry.tableparameter, data_entry.value)
            # rel_key = db.session(Relationship).filter(Relationship.fk_rel.like(f"{tableKeyName}%"), Relationship.entry_ref_pk=e_list.primary_key_value).first()
            
            rel_stmt = db.select(Relationship).filter_by(
                entry_ref_pk=e_list.primary_key_value, 
                foreign_key_rel_id=fk_ref_table.id)\
                .options(
                    selectinload(Relationship.entrylists).selectinload(EntryList.entries).joinedload(Entry.tableparameter), 
                    joinedload(Relationship.child_table).joinedload(Table.api)
                )
            rels = db.session.scalars(rel_stmt).all()
            rel_key_data = {} # format {"posts":[..]}
        

            
            for rel in rels:
                # child_tables.append(rel.child_table)
                fk_rel_name = f"{rel.child_table.api.name.lower()}_{rel.child_table.name.lower()}s"
                rel_key_data[fk_rel_name] = []
                for e_list_rel in rel.entrylists:
                    rel_data = {ent.tableparameter.name: parse_value(ent.tableparameter, ent.value) for ent in e_list_rel.entries}
                    rel_key_data[fk_rel_name].append(rel_data) # <api_name>_<model_name>s
            data["relationships"] = rel_key_data

            # set_user_api_cache(cache_key, data, api.id, table.name, child_tables)
            return format_response(data=data)
        except Exception as e:
            return format_response(status="error", message="Internal error", code=500)
