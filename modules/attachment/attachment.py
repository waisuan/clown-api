from bottle import Bottle, request, response, abort, JSONPlugin, static_file
from geventwebsocket import WebSocketError
import os, json, io
from time import sleep
from bson import json_util
from cleanr import Cleanr
import helpr

static_dir = './static'

cleanr = Cleanr(static_dir)
cleanr.daemon = True
cleanr.start()

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


@app.route('/<id>', method='GET')
def get_attachment(id):
    in_file = None
    try:
        in_file = db_mgr.get_attachment(id)
        with open(os.path.join(static_dir, in_file.filename),
                  "wb") as out_file:
            out_file.write(in_file.read())
        custom_response = static_file(in_file.filename,
                                      root=static_dir,
                                      mimetype='auto',
                                      download=True)
        custom_response.set_header('Access-Control-Allow-Origin', '*')
        custom_response.set_header('Access-Control-Expose-Headers',
                                   'Content-Disposition')
        return custom_response
    except:
        response.status = 404
        return
    finally:
        if in_file is not None:
            cleanr.add_to_queue(in_file.filename)


@app.route('/<id>', method='PUT')
def insert_attachment(id):
    attachment = request.files.get('attachment')
    in_mem_attachment = io.BytesIO()
    attachment.save(in_mem_attachment, True)
    in_mem_attachment.seek(0)
    filename = attachment.filename
    return db_mgr.insert_attachment(id, in_mem_attachment, filename)
