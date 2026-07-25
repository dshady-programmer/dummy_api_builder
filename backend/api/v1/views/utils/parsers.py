import bleach
from ast import literal_eval
def parse_value(tb_parameter, value):
    datatype = tb_parameter.data_type.name
    # consts = [c.name.value for c in tb_parameter.constraints]
    # if "default" in consts:
    #     value = tb_parameter.default_value
    print("datatype", datatype, value)
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


def csv_file_parser(csv_file, table, remaining_rows, delimiter=",", encoding='utf-8'):
    import csv
    import io
    from models.user import MAX_ROWS_FOR_CSV
    entries = []
    
    try:
        max_column = len(table.table_parameters)
        csv_content = io.TextIOWrapper(csv_file.stream, encoding=encoding, newline="")
        if delimiter:
            reader = csv.DictReader(csv_content, delimiter=delimiter)
        else:
            reader = csv.DictReader(csv_content)
        row_count = 1
        for row in reader:
            if row_count > MAX_ROWS_FOR_CSV or row_count > remaining_rows:
                break
            if len(row) > max_column:
                return None, f"CSV file has more columns than the table '{table.name}' allows"
            entries.append(row)
            row_count += 1
        return entries, None
    except Exception as e:
        return None, "Failed to parse CSV file"
