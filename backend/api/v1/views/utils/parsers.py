import bleach
from ast import literal_eval
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
            return literal_eval(value)
        return str(value)
    except:
        return None
    

def html_clean_value(value):
    ALLOWED_TAGS = ['b', 'i', 'strong', 'em', 'a', 'span', 'p', 'ul', 'ol', 'li', 'br']
    ALLOWED_ATTRS = {'a': ['href', 'title', 'target'], '*': ['class', 'id']}
    value = str(value)
    # Clean HTML to allow only certain tags/attributes
    clean_value = bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return clean_value