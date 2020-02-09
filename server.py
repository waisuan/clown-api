from gevent import monkey
monkey.patch_all()
import bottle, os
from bottle import run
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from cleanr import Cleanr
from modules.machine import machine
from modules.attachment import attachment

route_prefix = '/clown-api'

app = bottle.app()
app.mount(route_prefix + '/machines', machine.app)
app.mount(route_prefix + '/attachment', attachment.app)
if os.environ.get('APP_LOCATION') == 'heroku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), server='gevent', handler_class=WebSocketHandler)
else:
    run(host='localhost', port=8080, debug=True, server='gevent', handler_class=WebSocketHandler)
attachment.cleanr.stop()
attachment.cleanr.join()
