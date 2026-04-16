from chalice import Chalice
import requests
import boto3

app = Chalice(app_name='discord-bot-api')


@app.route('/')
def index():
    return {"methods": ["weather", "jokes", "ezra"]}

@app.route('/bot/{name}')
def hello_bot(name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('cloud-bots')
    response = table.get_item(Key={'botname': name})
    return response.get('Item', {})

@app.route('/register', methods=['POST'])
def add_bot():
    body = app.current_request.json_body
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('cloud-bots')
    table.put_item(Item={
        'user':    body['user'].strip(),
        'botname': body['botname'].strip(),
        'boturl':  body['boturl'].strip(),
    })
    return {'status': 'created', 'botname': body['botname'].strip()}


# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
