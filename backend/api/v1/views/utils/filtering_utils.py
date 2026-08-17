from dateutil.parser import parse 
from ast import literal_eval

def generate_suffixes(tp_name):
    VALID_FILTER_SUFFIXES = [
        "__lt",
        "__gt",
        "__lte",
        "__gte",
        "__startswith",
        "__endswith",
        "__like",
        "__ilike",
        "__istartswith",
        "__iendswith",
        "__iexact",
        "__not", # opposite of the default filter behavior, e.g if the default filter is to include only entries that match the filter, this would exclude those entries that match the filter
        "__inot", # case insensitive version of __not
        "__in" # filter to include only entries that matches a comma separated check_value
    ]
    tp_names = [tp_name]
    for suffix in VALID_FILTER_SUFFIXES:
        tp_names.append(f"{tp_name}{suffix}")
    return tp_names 

def filter_validation(tp_name, datatype, value, check_value):
    try:
        if tp_name.endswith("__lt"):
            if datatype == "integer":
                return int(check_value) > int(value)
            if datatype == "decimal":
                return float(check_value) > float(value)
            if datatype in ["date", "datetime"]:
                return parse(check_value) > parse(value)
        elif tp_name.endswith("__lte"):
            if datatype == "integer":
                return  int(check_value) >= int(value)
            if datatype == "decimal":
                return float(check_value) >= float(value)
            if datatype in ["date", "datetime"]:
                return parse(check_value) >= parse(value)
        elif tp_name.endswith("__gt"):
            if datatype == "integer":
                return int(check_value) < int(value)
            if datatype == "decimal":
                return float(check_value) < float(value)
            if datatype in ["date", "datetime"]:
                return parse(check_value) < parse(value)
        elif tp_name.endswith("__gte"):
            if datatype == "integer":
                return  int(check_value) <= int(value)
            if datatype == "decimal":
                return float(check_value) <= float(value)
            if datatype in ["date", "datetime"]:
                return parse(check_value) <= parse(value)
        elif tp_name.endswith("__startswith"):
            if datatype in ["text", "string"]:
                return str(value).startswith(str(check_value))
        elif tp_name.endswith("__endswith"):
            if datatype in ["text", "string"]:
                return str(value).endswith(str(check_value))
        elif tp_name.endswith("__istartswith"):
            if datatype in ["text", "string"]:
                return str(value).lower().startswith(str(check_value).lower())
        elif tp_name.endswith("__iendswith"):
            if datatype in ["text", "string"]:
                return str(value).lower().endswith(str(check_value).lower())
        elif tp_name.endswith("__like"):
            if datatype in ["text", "string"]:
                return str(check_value) in str(value)    
        elif tp_name.endswith("__ilike"):
            if datatype in ["text", "string"]:
                return str(check_value).lower() in str(value).lower()
        
        elif tp_name.endswith("__iexact"):
            if datatype in ["text", "string"]:
                return str(check_value).lower() == str(value).lower()
        elif tp_name.endswith("__not") or tp_name.endswith("__inot"):
            if datatype == "boolean":
                ev_check_val = literal_eval(check_value.capitalize())
                ev_val = literal_eval(value)
                if type(ev_check_val) == bool and type(ev_val) == bool:
                    return ev_val != ev_check_val
            if tp_name.endswith("__inot"):
                return str(check_value).lower() != str(value).lower()
            return str(check_value) != str(value)

        elif tp_name.endswith("__in"):
            check_values = [
                literal_eval(v.capitalize())
                if datatype == "boolean" else 
                int(v) if datatype == "integer" else
                float(v) if datatype == "decimal" else
                v.strip().lower() 
                for v in check_value.split(",")[:30] if v.strip()
            ] # Limit to 30 values
            if datatype == "boolean":
                ev_val = literal_eval(value)
                if type(ev_val) == bool:
                    return ev_val in check_values
            elif datatype == "integer":
                return int(value) in check_values
            elif datatype == "decimal":
                return float(value) in check_values
            return str(value).lower() in check_values
            
        else:
            if datatype == "boolean":
                ev_check_val = literal_eval(check_value.capitalize())
                ev_val = literal_eval(value)
                if type(ev_check_val) == bool and type(ev_val) == bool:
                    return ev_val == ev_check_val
            elif datatype == "integer":
                return int(check_value) == int(value)
            return check_value == value
    except:
        return False
    else:
        return False

    
    

# def query_filter(tp_name, args, datatype, value, found_valid_arg, filter_in):
#     tp_names = generate_suffixes(tp_name)
#     for name in tp_names:

#         if name in args:

#             found_valid_arg = True
#             if not filter_validation(name, datatype, value, args[name]):
#                 filter_in = False
#     return found_valid_arg, filter_in


def query_filter(entrylist, valid_args, args, data_type_map, filter_type):
    filter_in = True if filter_type == "&" else False
    for arg in valid_args:
        tp_name = arg['tp_name']
        tp_suffix = arg['tp_suffix']
        datatype = data_type_map[tp_name]
        value = entrylist[tp_name]

        if filter_type == "&":
            if not filter_validation(tp_suffix, datatype, value, args[tp_suffix]):
                filter_in = False
        else:
            if filter_validation(tp_suffix, datatype, value, args[tp_suffix]):
                filter_in = True
    return filter_in
    
    
    

    


