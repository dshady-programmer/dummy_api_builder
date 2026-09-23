from dateutil.parser import parse 
from ast import literal_eval

def generate_suffixes(tp_name):
    VALID_FILTER_SUFFIXES = [
        "__lt",
        "__gt",
        "__lte",
        "__gte",
        "__iexact",
        "__startswith",
        "__istartswith",
        "__endswith",
        "__iendswith",
        "__like", # match substrings
        "__ilike",
        "__like_any", # match substrings, for each list of strings
        "__ilike_any",
        "__not", # opposite of the default filter behavior, e.g if the default filter is to include only entries that match the filter, this would exclude those entries that match the filter
        "__inot", # case insensitive version of __not
        "__in", # filter to include only entries that matches a comma separated check_value
        "__notin", # filter to exclude entries that matches a comma separated check_value
        "__isnull", # filter to include only entries that have a null value for the table parameter
    ]
    tp_names = [tp_name]
    for suffix in VALID_FILTER_SUFFIXES:
        tp_names.append(f"{tp_name}{suffix}")
    return tp_names 

def filter_validation(tp_name, datatype, value, check_value):
    check_value = check_value.strip()
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
            
        elif tp_name.endswith("__startswith") or tp_name.endswith("__istartswith"):
            case_insensitive = tp_name.endswith("__istartswith")
            if datatype in ["text", "string"]:
                if value is None:
                    return False
                return (
                    str(value).lower().startswith(str(check_value).lower()) 
                        if case_insensitive
                        else 
                    str(value).startswith(str(check_value))
                )
            
        elif tp_name.endswith("__endswith") or tp_name.endswith("__iendswith"):
            case_insensitive = tp_name.endswith("__iendswith")
            if datatype in ["text", "string"]:
                if value is None:
                    return False
                return (
                    str(value).lower().endswith(str(check_value).lower())
                        if case_insensitive 
                        else  
                    str(value).endswith(str(check_value))
                )
        elif tp_name.endswith("__like") or tp_name.endswith("__ilike"):
            case_insensitive = tp_name.endswith("__ilike")
            if datatype in ["text", "string"]:
                if value is None:
                    return False
                return (
                    str(check_value).lower() in str(value).lower() 
                        if case_insensitive 
                        else 
                    str(check_value) in str(value)    
                )

        elif tp_name.endswith("__like_any") or tp_name.endswith("__ilike_any"):
            case_insensitive = tp_name.endswith("__ilike_any")
            if datatype not in ["text", "string"]:
                return False
            match = False

            if value is None:
                return match
        
            for v in check_value.split(",")[:30]:  # Limit to 30 values
                v = v.strip()
                if not v:
                    continue
                match = (
                    str(value).lower() in str(v).lower() 
                        if case_insensitive 
                        else 
                    str(value) in str(v)
                )
                if match:
                    return match
                    
            return match
        
        elif tp_name.endswith("__iexact"):
            if datatype in ["text", "string"]:
                if value is None:
                    return False
                return str(check_value).lower() == str(value).lower()
        elif tp_name.endswith("__not") or tp_name.endswith("__inot"):
            case_insensitive = tp_name.endswith("__inot")
            if value is None:
                return True
            if datatype == "boolean":
                ev_check_val = literal_eval(check_value.capitalize())
                return value != ev_check_val
            if case_insensitive:
                return str(check_value).lower() != str(value).lower()
            return str(check_value) != str(value)

        elif tp_name.endswith("__in") or tp_name.endswith("__notin"):
            check_for_in = tp_name.endswith("__in")
            match = False

            if value is None:
                return match if check_for_in else not match
        
            
            for v in check_value.split(",")[:30]:  # Limit to 30 values
                v = v.strip()
                if not v:
                    continue
                if datatype == "boolean":
                    try:
                        ch_val = literal_eval(v.capitalize())
                        if type(ch_val) == bool:
                            match = ch_val == check_value
                    except:
                        continue
                elif datatype == "integer":
                    try:
                        match = int(value) == int(v)
                    except ValueError:
                        continue
                elif datatype == "decimal":
                    try:
                        match = float(value) == float(v)
                    except ValueError:
                        continue
                else:  # For string and text types
                    match = str(value).lower() == str(v).lower()
                if match:
                    return match if check_for_in else not match
                    
            return match if check_for_in else not match

        elif tp_name.endswith("__isnull"):
            if check_value.lower() == "true":
                return value is None
            elif check_value.lower() == "false":
                return value is not None
            else:
                return False  # Invalid check_value for __isnull,
        
        else:
            if value is None:
                return False

            if datatype == "boolean":
                ev_check_val = literal_eval(check_value.capitalize())
                return value == ev_check_val
            elif datatype == "integer":
                return int(check_value) == int(value)
            elif datatype == "decimal":
                return float(check_value) == float(value)
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
    
    
    

    


