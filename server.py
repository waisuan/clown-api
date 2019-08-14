from gevent import monkey
monkey.patch_all()
import json, bottle, os, io, helpr
from bottle import route, run, template, response, hook, JSONPlugin, request, static_file, abort
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from DatabaseManager import DatabaseManager
from bson import json_util
# from cherrypy import wsgiserver
from threading import Thread
from cleanr import Cleanr
from time import sleep


route_prefix = '/clown-api'
static_dir = './static'
db_mgr = DatabaseManager(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'), os.environ.get('DB_NAME', 'emblem'))
cleanr = Cleanr(static_dir)


@hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Accept-Encoding, Content-Disposition, Content-Length, Accept-Ranges, Content-Range'


@route('/', method='OPTIONS')
@route('/<path:path>', method='OPTIONS')
def options_handler(path=None):
    return


@route(route_prefix + '/machines')
@route(route_prefix + '/machines/<limit:int>')
@route(route_prefix + '/machines/<limit:int>/<last_batch_fetched:int>')
@route(route_prefix + '/machines/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>')
def get_machines(limit=None, last_batch_fetched=0, sort_by=None, sort_order=None):
    return db_mgr.get_machines(limit, last_batch_fetched, sort_by, sort_order)


@route(route_prefix + '/machines/due/<status>')
@route(route_prefix + '/machines/due/<status>/<limit:int>')
@route(route_prefix + '/machines/due/<status>/<limit:int>/<last_batch_fetched:int>')
@route(route_prefix + '/machines/due/<status>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>')
def get_due_machines(status, limit=None, last_batch_fetched=0, sort_by=None, sort_order=None):
    print(status)
    return db_mgr.get_machines(limit, last_batch_fetched, sort_by, sort_order, status)


@route(route_prefix + '/machines/search/<property>')
@route(route_prefix + '/machines/search/<property>/<limit:int>')
@route(route_prefix + '/machines/search/<property>/<limit:int>/<last_batch_fetched:int>')
@route(route_prefix + '/machines/search/<property>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>')
def get_machines_by_property(property, limit=None, last_batch_fetched=0, sort_by=None, sort_order=None):
    return db_mgr.get_machines_by_property(property, limit, last_batch_fetched, sort_by, sort_order)


@route(route_prefix + '/machine', method='POST')
def insert_machine():
    if db_mgr.insert_machine(request.json):
        response.status = 200
    else:
        response.status = 404
    return


@route(route_prefix + '/machine/<id>', method='PUT')
def update_machine(id):
    if db_mgr.update_machine(id, request.json):
        response.status = 200
    else:
        response.status = 404
    return


@route(route_prefix + '/machine/<id>', method='DELETE')
def delete_machine(id):
    if db_mgr.delete_machine(id):
        response.status = 200
    else:
        response.status = 404
    return


@route(route_prefix + '/attachment/<id>', method='PUT')
def insert_attachment(id):
    attachment = request.files.get('attachment')
    in_mem_attachment = io.BytesIO()
    attachment.save(in_mem_attachment, True)
    in_mem_attachment.seek(0)
    filename = attachment.filename
    return db_mgr.insert_attachment(id, in_mem_attachment, filename)


@route(route_prefix + '/attachment/<id>')
def get_attachment(id):
    in_file = None
    try:
        in_file = db_mgr.get_attachment(id)
        with open(os.path.join(static_dir, in_file.filename), "wb") as out_file:
            out_file.write(in_file.read())
        custom_response = static_file(in_file.filename, root=static_dir, mimetype='auto', download=True)
        custom_response.set_header('Access-Control-Allow-Origin', '*')
        custom_response.set_header('Access-Control-Expose-Headers', 'Content-Disposition')
        return custom_response
    except:
        response.status = 404
        return
    finally:
        if in_file is not None:
            cleanr.add_to_queue(in_file.filename)


@route(route_prefix + '/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    while True:
        try:
            num = db_mgr.get_num_of_due_machines()
            wsock.send(json.dumps(num))
            sleep(60)
        except WebSocketError:
            break


app = bottle.app()
app.install(JSONPlugin(json_dumps=lambda body: json.dumps(body, default=json_util.default)))
cleanr.start()
if os.environ.get('APP_LOCATION') == 'heroku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), server='gevent', handler_class=WebSocketHandler)
else:
    run(host='localhost', port=8080, debug=True, server='gevent', handler_class=WebSocketHandler)
cleanr.stop()
cleanr.join()
