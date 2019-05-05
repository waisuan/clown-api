import json, bottle, os, io, helpr
from bottle import route, run, template, response, hook, JSONPlugin, request, static_file
from DatabaseManager import DatabaseManager
from bson import json_util
from cherrypy import wsgiserver
from threading import Thread
from cleanr import Cleanr


route_prefix = '/clown-api'
static_dir = './static'
db_mgr = DatabaseManager(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'), os.environ.get('DB_NAME', 'emblem'))
cleanr = Cleanr(static_dir)


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
def get_machines(limit=None, last_batch_fetched=0, sort_by=None, sort_order=None):
    print('get_machines')
    return db_mgr.get_machines(limit, last_batch_fetched, sort_by, sort_order)


@route(route_prefix + '/machines/search/<property>')
@route(route_prefix + '/machines/search/<property>/<limit:int>')
@route(route_prefix + '/machines/search/<property>/<limit:int>/<last_batch_fetched:int>')
@route(route_prefix + '/machines/search/<property>/<limit:int>/<last_batch_fetched:int>/<sort_by>/<sort_order>')
def get_machines_by_property(property, limit=None, last_batch_fetched=0, sort_by=None, sort_order=None):
    print('get_machines_by_property')
    return db_mgr.get_machines_by_property(property, limit, last_batch_fetched, sort_by, sort_order)


@route(route_prefix + '/machine/<id>', method='PUT')
def update_machine(id):
    # print(request.json)
    # print(request.forms['hello'])
    attachment = request.files.get('attachment')
    if (attachment is not None):
        in_mem_attachment = io.BytesIO()
        attachment.save(in_mem_attachment, True)
        in_mem_attachment.seek(0)
        filename = attachment.filename
    if db_mgr.update_machine(id, request.forms, in_mem_attachment, filename):
        response.status = 200
    else:
        response.status = 400
    return


@route(route_prefix + '/attachment/<id>')
def get_attachment(id):
    try:
        in_file = db_mgr.get_attachment(id)
        with open(os.path.join(static_dir, in_file.filename), "wb") as out_file:
            out_file.write(in_file.read())
        return static_file(in_file.filename, root=static_dir)
    finally:
        cleanr.add_to_queue(in_file.filename)



app = bottle.app()
app.install(JSONPlugin(json_dumps=lambda body: json.dumps(body, default=json_util.default)))
cleanr.start()
if os.environ.get('APP_LOCATION') == 'heroku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), server='cherrypy')
else:
    run(host='localhost', port=8080, debug=True)
cleanr.stop()
cleanr.join()
