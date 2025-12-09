from models import TableParameter,Api, Table,Constraint, db
from .validate import validate_constraint, validate_dtType, validate_name


def create_table_parameter(param, table, tableparam_names, user):
    primary_key_present = False
    param_name = param.get("name")
    param_dt = param.get("datatype")
    param_dt_length = param.get("dt_length")
    constraints = param.get("constraints") or []
    if type(constraints) != list:
        raise Exception({"error": "Invalid constraints type"})
    constraints = set(constraints) # incase of duplicate values.

    if not param_name:
        raise Exception({"error": "Table parameter name can't be empty"})
    if param_name in tableparam_names:
        # First check if the table param of such name already exist on the table
        """
        This check is done for events where table attribute is passed 2ce in the list
        just like there can't be two model attribute of the same name
        like you can't have 
        name=String()
        and then..
        name = Integer()
        """
        
        raise Exception({"error": f"Duplicate name '{param_name}' of table parameter, it must be unique"})
    if not validate_dtType(param_dt):
        # validate the data type
        # Technically this check won't be triggered if the api is used from the frontend

        raise Exception({"error": "invalid data type"})
    if not validate_name(param_name):
        # validate the model field name
        # Technically this check won't be triggered if the api is used from the frontend
        raise Exception({"error": "invalid name(must be a valid python identifier) and not a python keyword"})
    try:
        if param_dt_length and param_dt in ["string", "text"]: # if maximum length is set for the model field
            param_dt_length = int(param_dt_length)
        else:
            param_dt_length = None
    except ValueError: 
        # In the case the value passed is not an integer
        param_dt_length = None

    # If everything goes perfectly go ahead and create the model field relating to the user table/model and the api
    p = TableParameter(name=param_name, data_type=param_dt, dataType_length=param_dt_length)
    table.table_parameters.append(p)
    # keep track of the param_name to avoid duplication later along the line
    tableparam_names.add(param_name)
    if "primary_key" in constraints:
        constraints.add("unique") # add unique to constraint if it's a primary key.
        if "nullable" in constraints:
            # You definitely can't have a field that is the PK and still allow a null value
            constraints.remove("nullable") 
    for const in constraints:
        # There can be more than one constraints for a model field
        if not validate_constraint(const):
            # Check if the constraints are valid
            raise Exception({"error": "invalid constraint"})
        if const == "foreign_key":
            fk_rf = param.get("foreign_key_rf") #expected format(api.table)
            if not fk_rf:
                raise Exception({"error": "Expected a foreign key reference field."})
            f_api, f_table = fk_rf.split(".") # Check if the reference api and model are valid for it to be a foreign key field
            r_api = Api.query.filter_by(name=f_api, user_id=user.id).first()
            if not r_api:
                raise Exception({"error": "Api name referenced in the foreign key doesn't exist"})
            r_table = Table.query.filter_by(name=f_table, api_id=r_api.id).first()
            if not r_table:
                raise Exception({"error", "Table name referenced doesn't exist"})
            p.foreign_key_reference_field = fk_rf
        if const == "primary_key":
            primary_key_present = True
            p.primary_key = True
        
        get_c = Constraint.query.filter_by(name=const).first()
        if get_c:
            p.constraints.append(get_c)
        else:
            p.constraints.append(Constraint(name=const))
    return primary_key_present


def update_table_parameter(param, tableparam, tableparam_names, user):
    primary_key_present = False
    param_name = param.get("name")
    param_dt = param.get("datatype")
    param_dt_length = param.get("dt_length")
    constraints = param.get("constraints") or []
    if type(constraints) != list:
        raise Exception({"error": "Invalid constraints type"})
    constraints = set(constraints) # incase of duplicate values.

   
    
    # """
    # in the next version you should be able to add more fields to a model if data already exists
    # but would require a default value to prepopulate previously created module.
    # """
    # if entry_present:
    #     return jsonify({"error": "You cannot edit or add new field to the model when it already has data"}), 400
    # if validate_name(param_name) and param_dt and validate_dtType(param_dt):
    #     p = TableParameter(name=param_name, table_id=get_table.id, data_type=param_dt)

    # check update the param name
    if param_name:
        if param_name not in tableparam_names and validate_name(param_name):
            tableparam.name = param_name
            tableparam_names.add(name)

    if param_dt and validate_dtType(param_dt):
        tableparam.data_type = param_dt
    
    print(param_dt)
    if param_dt_length and param_dt in ["string", "text"]:
        try:
            param_dt_length = int(param_dt_length)
            tableparam.dataType_length = param_dt_length
        except ValueError:
            pass
    else:
        tableparam.dataType_length = None
            
    # else:
    #     if entry_present:
    #         if "nullable" in constraints:
    #             if "primary_key" in [con.name.value for con in p.constraints]:
    #                 continue
    #             get_c = Constraint.query.filter_by(name="nullable").first()
    #             if get_c:
    #                 p.constraints.append(get_c)
    #             else:
    #                 p.constraints.append(Constraint(name="nullable"))
    #         continue
    #     # if validate_name(param_name):
        #     p.name = param_name
    
    if "primary_key" in constraints:
        constraints.add("unique")
        if "nullable" in constraints:
            constraints.remove("nullable")

    tableparam.constraints.clear()
    for const in constraints:
        if not validate_constraint(const):
            raise Exception({"error": "invalid constraint"})
        if const == "foreign_key":
            fk_rf = param.get("foreign_key_rf") #expected format(api.table) 
            if not fk_rf:
                raise Exception({"error": "Expected a foreign key reference field."})
            f_api, f_table = fk_rf.split(".")
            r_api = Api.query.filter_by(name=f_api, user_id=user.id).first()
            if not r_api:
                raise Exception({"error": "Api name referenced in the foreign key doesn't exist"})
            r_table = Table.query.filter_by(name=f_table, api_id=r_api.id).first()
            if not r_table:
                raise Exception({"error", "Table name referenced doesn't exist"})
            # r_field = TableParameter.query.filter_by(name=field, table_id=r_table.id).first()
            # if not r_field:
            #     continue
            tableparam.foreign_key_reference_field = fk_rf
        if const == "primary_key":
            tableparam.primary_key = True
            primary_key_present = True
        
        get_c = Constraint.query.filter_by(name=const).first()
        if get_c:
            tableparam.constraints.append(get_c)
        else:
            tableparam.constraints.append(Constraint(name=const))
    return primary_key_present




def parse_and_create_tableparameters(table_parameters, new_table, user):
    primary_key_present = False

    tableparam_names = set()
    try:
        for param in table_parameters:
           is_primary_key = create_table_parameter(param, new_table, tableparam_names, user)
           if not primary_key_present:
               primary_key_present = is_primary_key
        if not primary_key_present:
            raise Exception({"error": "Table must contain atleast one primary key"})
    except Exception as e:
        error = e.args[0]
        db.session.rollback()
        if type(error) == dict and "error" in error:
            return error 
        return {"error": "Something went wrong"}
    
    else:
        db.session.commit()
        return {"id": new_table.id, "name": new_table.name, "desc": new_table.description}




def parse_and_update_tableparameters(table_parameters, table, user):
    primary_key_present = False

    tableparam_names = set()
    existing_table_parameter_mapper = {}

    for existing_tblp in table.table_parameters:
        tableparam_names.add(existing_tblp.name)
        existing_table_parameter_mapper[existing_tblp.id] = existing_tblp
    
    try:
        print(existing_table_parameter_mapper)
        for param in table_parameters:
            print(param)

            param_id = param.get("index")
            print(param_id)
            if param_id in existing_table_parameter_mapper:
                is_primary_key = update_table_parameter(param, existing_table_parameter_mapper[param_id], tableparam_names, user)
            else:
                is_primary_key = create_table_parameter(param, table, tableparam_names, user)
            if not primary_key_present:
                primary_key_present = is_primary_key
        if not primary_key_present:
            raise Exception({"error": "Table must contain atleast one primary key"})
    except Exception as e:
        error = e.args[0]
        db.session.rollback()
        if type(error) == dict and "error" in error:
            return error 
        return {"error": "Something went wrong"}
    
    else:
        db.session.commit()
        return {"id": table.id, "name": table.name, "desc": table.description}
