from flask import jsonify
def format_response(status="success", message=None, data=None, code=200, format_json=True):
    
    response = {"status": status}
    if message:
        response['message'] = message

    if data:
        response['data'] = data

    if format_json:
        return jsonify(response), code
    return response, code
