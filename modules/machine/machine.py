from bottle import Bottle, request, response, abort, JSONPlugin, auth_basic
from geventwebsocket import WebSocketError
import os, json
from time import sleep
from bson import json_util
import helpr

app = Bottle()
app.install(
    JSONPlugin(
        json_dumps=lambda body: json.dumps(body, default=json_util.default)))
db_mgr = helpr.get_db_mgr()


@app.hook('before_request')
def authenticate():
    if request.method == 'OPTIONS':
        return
    token = request.headers.get('Authorization', "").replace('Bearer ', '')
    if not helpr.validate_jwt_token(token):
        response.status = 401
        return


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


@app.route('/', method='GET')
@app.route('/<limit:int>', method='GET')
@app.route('/<limit:int>/<last_batch_fetched:int>', method='GET')
@app.route('/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>',
           method='GET')
def get_machines(limit=None,
                 last_batch_fetched=0,
                 sort_by=None,
                 sort_order=None):
    return db_mgr.get_machines(limit, last_batch_fetched, sort_by, sort_order)


@app.route('/due/<status>', method='GET')
@app.route('/due/<status>/<limit:int>', method='GET')
@app.route('/due/<status>/<limit:int>/<last_batch_fetched:int>', method='GET')
@app.route(
    '/due/<status>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>',
    method='GET')
def get_due_machines(status,
                     limit=None,
                     last_batch_fetched=0,
                     sort_by=None,
                     sort_order=None):
    return db_mgr.get_machines(limit, last_batch_fetched, sort_by, sort_order,
                               status)


@app.route('/search/<property>', method='GET')
@app.route('/search/<property>/<limit:int>', method='GET')
@app.route('/search/<property>/<limit:int>/<last_batch_fetched:int>',
           method='GET')
@app.route(
    '/search/<property>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>',
    method='GET')
def get_machines_by_property(property,
                             limit=None,
                             last_batch_fetched=0,
                             sort_by=None,
                             sort_order=None):
    return db_mgr.get_machines_by_property(property, limit, last_batch_fetched,
                                           sort_by, sort_order)


@app.route('/', method='POST')
def insert_machine():
    if db_mgr.insert_machine(request.json):
        response.status = 200
    else:
        response.status = 404
    return


@app.route('/<id>', method='PUT')
def update_machine(id):
    if db_mgr.update_machine(id, request.json):
        response.status = 200
    else:
        response.status = 404
    return


@app.route('/<id>', method='DELETE')
def delete_machine(id):
    if db_mgr.delete_machine(id):
        response.status = 200
    else:
        response.status = 404
    return


@app.route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    while True:
        try:
            num = db_mgr.get_num_of_due_machines()
            wsock.send(json.dumps(num))
            sleep(3600)
        except WebSocketError:
            break
