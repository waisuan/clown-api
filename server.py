import json
import bottle
from bottle import route, run, template, response, hook, JSONPlugin, request
from DatabaseManager import DatabaseManager
from bson import json_util
from cherrypy import wsgiserver
import os
from pprint import pprint

route_prefix = '/clown-api'
db_mgr = DatabaseManager(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'), os.environ.get('DB_NAME', 'emblem'))


@hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
    #response.headers['Content-Type'] = 'application/json'


@route('/', method='OPTIONS')
@route('/<path:path>', method='OPTIONS')
def options_handler(path=None):
    return


@route(route_prefix + '/machines')
@route(route_prefix + '/machines/<limit:int>')
@route(route_prefix + '/machines/<limit:int>/<last_batch_fetched:int>')
@route(route_prefix + '/machines/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>')
def get_machines(limit=None, last_batch_fetched=0, sort_by=0, sort_order=0):
    print('get_machines')
    return db_mgr.get_machines(limit, last_batch_fetched, sort_by, sort_order)


@route(route_prefix + '/machines/search/<property>')
@route(route_prefix + '/machines/search/<property>/<limit:int>')
@route(route_prefix + '/machines/search/<property>/<limit:int>/<last_batch_fetched:int>')
@route(route_prefix + '/machines/search/<property>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>')
def get_machines_by_property(property, limit=None, last_batch_fetched=0, sort_by=0, sort_order=0):
    print('get_machines_by_property')
    return db_mgr.get_machines_by_property(property, limit, last_batch_fetched, sort_by, sort_order)


@route(route_prefix + '/machine/<id>', method='PUT')
def update_machine(id):
    print(id)
    print(request.json)
    #print(request.body.read())
    if db_mgr.update_machine(id, request.json):
        response.status = 200
    else:
        response.status = 400
    return


app = bottle.app()
app.install(JSONPlugin(json_dumps=lambda body: json.dumps(
    body, default=json_util.default)))
if os.environ.get('APP_LOCATION') == 'heroku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), server='cherrypy')
else:
    run(host='localhost', port=8080, debug=True)
