import json
import bottle
from bottle import route, run, template, response, hook, JSONPlugin
from DatabaseManager import DatabaseManager
from bson import json_util
from cherrypy import wsgiserver
import os

route_prefix = '/clown-api'
db_mgr = DatabaseManager(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'), os.environ.get('DB_NAME', 'emblem'))


@hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'


@route(route_prefix + '/machines/search/<property>')
@route(route_prefix + '/machines/search/<property>/<limit>')
@route(route_prefix + '/machines/search/<property>/<limit>/<last_batch_fetched>')
@route(route_prefix + '/machines/search/<property>/<limit>/<last_batch_fetched>/<sort_by>/<sort_order>')
def get_machines_by_property(property, limit=None, last_batch_fetched=0, sort_by=0, sort_order=0):
    print('get_machines_by_property')
    return db_mgr.get_machines_by_property(property, limit, last_batch_fetched, sort_by, sort_order)


@route(route_prefix + '/machines/id/<id>')
def get_machine_by_id(id):
    return {'data': db_mgr.get_machine_by_id(id)}
    

@route(route_prefix + '/machines')
@route(route_prefix + '/machines/<limit>')
@route(route_prefix + '/machines/<limit>/<last_batch_fetched>')
@route(route_prefix + '/machines/<limit>/<last_batch_fetched>/<sort_by>/<sort_order>')
def get_machines(limit=None, last_batch_fetched=0, sort_by=0, sort_order=0):
    print('get_machines')
    return db_mgr.get_machines(limit, last_batch_fetched, sort_by, sort_order)


app = bottle.app()
app.install(JSONPlugin(json_dumps=lambda body: json.dumps(
    body, default=json_util.default)))
if os.environ.get('APP_LOCATION') == 'heroku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), server='cherrypy')
else:
    run(host='localhost', port=8080, debug=True, server='cherrypy')
