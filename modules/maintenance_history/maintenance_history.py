from bottle import Bottle, request, response, abort, JSONPlugin, HTTPError
from geventwebsocket import WebSocketError
import os, json
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
        raise HTTPError(401, Access_Control_Allow_Origin='*')


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


@app.route('/fetch/<machine_id>', method='GET')
@app.route('/fetch/<machine_id>/<limit:int>', method='GET')
@app.route('/fetch/<machine_id>/<limit:int>/<last_batch_fetched:int>',
           method='GET')
@app.route(
    '/fetch/<machine_id>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>',
    method='GET')
def get_history(machine_id,
                limit=None,
                last_batch_fetched=0,
                sort_by=None,
                sort_order=None):
    return db_mgr.get_history(machine_id, limit, last_batch_fetched, sort_by,
                              sort_order)


@app.route('/search/<machine_id>/<property>', method='GET')
@app.route('/search/<machine_id>/<property>/<limit:int>', method='GET')
@app.route(
    '/search/<machine_id>/<property>/<limit:int>/<last_batch_fetched:int>',
    method='GET')
@app.route(
    '/search/<machine_id>/<property>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>',
    method='GET')
def get_history_by_property(machine_id,
                            property,
                            limit=None,
                            last_batch_fetched=0,
                            sort_by=None,
                            sort_order=None):
    return db_mgr.get_history_by_property(machine_id, property, limit,
                                          last_batch_fetched, sort_by,
                                          sort_order)


@app.route('/', method='POST')
def insert_history():
    if db_mgr.insert_history(request.json):
        response.status = 200
    else:
        response.status = 404
    return


@app.route('/<id>', method='PUT')
def update_history(id):
    if db_mgr.update_history(id, request.json):
        response.status = 200
    else:
        response.status = 404
    return


@app.route('/<id>', method='DELETE')
def delete_history(id):
    if db_mgr.delete_history(id):
        response.status = 200
    else:
        response.status = 404
    return
