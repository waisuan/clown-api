from bottle import Bottle, request, response, JSONPlugin
from DatabaseManager import DatabaseManager
import os, json, datetime
from bson import json_util
import helpr
import jwt

app = Bottle()
app.install(
    JSONPlugin(
        json_dumps=lambda body: json.dumps(body, default=json_util.default)))
db_mgr = helpr.get_db_mgr()


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
    to_encode = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
    }
    token = jwt.encode(to_encode, 'secret', algorithm='HS256')
    return json.dumps({'token': token.decode('ascii')})


@app.route('/verify', method='POST')
def verify():
    token = request.json['token']
    try:
        jwt.decode(token, 'secret', algorithm='HS256')
        response.status = 200
    except:
        response.status = 400
    return
