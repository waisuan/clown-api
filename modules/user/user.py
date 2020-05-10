from bottle import Bottle, request, response, JSONPlugin
import os, json, datetime
from bson import json_util
import helpr
import jwt
import uuid
from modules.user.user_store import UserStore

app = Bottle()
app.install(
    JSONPlugin(
        json_dumps=lambda body: json.dumps(body, default=json_util.default)))
db_mgr = helpr.get_db_mgr()
user_store = UserStore()


@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers[
        'Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Authorization, Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Accept-Encoding, Content-Disposition, Content-Length, Accept-Ranges, Content-Range'


@app.route('/', method='OPTIONS')
@app.route('/<path:path>', method='OPTIONS')
def options_handler(path=None):
    return


@app.route('/create', method='POST')
def create():
    if db_mgr.create_user(request.json):
        response.status = 200
    else:
        response.status = 404
    return


@app.route('/login', method='POST')
def login():
    if not db_mgr.confirm_user(request.json):
        response.status = 404
        return
    username = request.json['username']
    token = helpr.create_jwt_token(username)
    user_store.store(username, token)
    return json.dumps({'token': token})


@app.route('/extend/<username>', method='POST')
def extend(username):
    curr_token = request.headers.get('Authorization',
                                     "").replace('Bearer ', '')
    if not user_store.contains(username, curr_token):
        response.status = 401
        return
    if not helpr.validate_jwt_token(curr_token):
        curr_token = helpr.create_jwt_token(str(uuid.uuid4()))
        user_store.store(username, curr_token)
    return json.dumps({'token': curr_token})
