from dateutil.parser import parse 

def filter_suffixes(tp_name):
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
        "__iexact"
    ]
    tp_names = [tp_name]
    for suffix in VALID_FILTER_SUFFIXES:
        tp_names.append(f"{tp_name}{suffix}")
    return tp_names 

def filter_validation(tp_name, datatype, value, check_value):
    
    try:
        if tp_name.endswith("__lt"):
            if datatype == "integer":
                return int(check_value) < int(value)
            if datatype in ["date", "datetime"]:
                return parse(check_value) < parse(value)
        elif tp_name.endswith("__lte"):
            if datatype == "integer":
                return  int(check_value) <= int(value)
            if datatype in ["date", "datetime"]:
                return parse(check_value) <= parse(value)
        elif tp_name.endswith("__gt"):
            if datatype == "integer":
                return int(check_value) > int(value)
            if datatype in ["date", "datetime"]:
                return parse(check_value) > parse(value)
        elif tp_name.endswith("__gte"):
            if datatype == "integer":
                return  int(check_value) >= int(value)
            if datatype in ["date", "datetime"]:
                return parse(value) >= parse(check_value)
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
            
        else:
            if datatype == "boolean":
                ev_check_val = eval(check_value)
                ev_val = eval(value)
                if type(ev_check_val) == bool and type(ev_val) == bool:
                    return ev_val == ev_check_val
            elif datatype == "integer":
                return int(check_value) == int(value)
            return check_value == value
    except:
        return False

    
    

def query_filter(tp_name, args, datatype, value):
    tp_names = filter_suffixes(tp_name)
    found_valid_arg = False
    filter_in = True

    for name in tp_names:
        if name in args:
            found_valid_arg = True
            if not filter_validation(name, datatype, value, args[name]):
                filter_in = False
    return found_valid_arg, filter_in

    
    
    

    


