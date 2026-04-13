import json
import boto3
from chalice import Chalice

app = Chalice(app_name='api-for-linecounts')

ddb = boto3.resource('dynamodb')
table = ddb.Table('s3-linecount')

@app.route('/')
def index():
    return {'hello': 'Neal'}

@app.route('/items', methods=['GET'])
def items():
    response = table.scan(Limit=100)
    return {'items': response.get('Items', [])}


@app.route('/items', methods=['POST'])
def create_item():
    body = app.current_request.json_body or {}
    fileid = body.get('fileid')
    line_count = body.get('line_count')
    if not fileid or line_count is None:
        return {'error': 'fileid and line_count are required'}
    table.put_item(Item={'fileid': fileid, 'line_count': int(line_count)})
    return {'status': 'ok', 'fileid': fileid, 'line_count': int(line_count)}



# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{fname}/{lname}')
# def hello_name(fname, lname):
#     # '/hello/james' -> {"hello": "james"}
#     return {'hello': fname + ' ' + lname}
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
