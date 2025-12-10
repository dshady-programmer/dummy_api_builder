
def parse_value(datatype, value):
    if datatype == "integer":
        return int(value)
    elif datatype == "boolean":
        return eval(value)
    return str(value)
    