
def parse_value(tb_parameter, value):
    datatype = tb_parameter.data_type.name
    # consts = [c.name.value for c in tb_parameter.constraints]
    # if "default" in consts:
    #     value = tb_parameter.default_value
    try:

        if not value:
            value = None
            return value
        if datatype == "integer":
            return int(value)
        elif datatype == "boolean":
            return eval(value)
        return str(value)
    except:
        return None
    