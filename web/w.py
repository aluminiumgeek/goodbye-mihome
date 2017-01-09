import os
import random
import sys

import psycopg2
import tornado.ioloop
import tornado.web
import tornado.websocket

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config
from .utils import format_value

conn = psycopg2.connect("dbname={} user={} password={}".format(config.DBNAME, config.DBUSER, config.DBPASS))


def get_cursor():
    global conn
    return conn.cursor()


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        cursor = get_cursor()
        cursor.execute('SELECT DISTINCT ON (sid) sid, temperature, humidity FROM ht ORDER BY sid, dt DESC')
        sensors_current = []
        sensors_data = {}

        for sid, temperature, humidity in cursor.fetchall():
            sensors_current.append({
                'sid': sid,
                'name': config.SENSORS.get(sid, sid),
                'temperature': format_value(temperature, split=True),  #'{:0.2f}'.format(temperature/100.0),
                'humidity': format_value(humidity, split=True)  #'{:0.2f}'.format(humidity/100.0)
            })

            sensors_data[sid] = {
                'labels': [],
                'datasets': [
                    {
                        'label': 'Temperature',
                        'data': [],
                        'borderColor': '#bf3d3d'
                    },
                    {
                        'label': 'Humidity',
                        'data': [],
                        'borderColor': '#b7bce5'
                    }
                ]
            }
            cursor.execute('SELECT sid, temperature, humidity, dt FROM ht WHERE sid = %s ORDER BY dt LIMIT 25', (sid,))

            for sid, temperature, humidity, dt in cursor.fetchall():
                sensors_data[sid]['labels'].append(dt.isoformat())
                sensors_data[sid]['datasets'][0]['data'].append(format_value(temperature))
                sensors_data[sid]['datasets'][1]['data'].append(format_value(humidity))

        bg_images = map(lambda x: '/static/img/bg/%s' % x, os.listdir(os.path.join(os.path.dirname(__file__), "static", "img", "bg")))
        bg_images = list(filter(lambda x: x.endswith('.jpg'), bg_images))

        self.render(
            "templates/index.html",
            sensors=config.SENSORS,
            sensors_current=sensors_current,
            sensors_data=sensors_data,
            bg_images=bg_images
        )


class UpdatesHandler(tornado.websocket.WebSocketHandler):

    socket_clients = set()

    def open(self):
        self.socket_clients.add(self)

    def on_close(self):
        self.socket_clients.remove(self)

    @classmethod
    def send_updates(cls, data):
        for client in cls.socket_clients:
            client.write_message(data)


def make_app():
    static_path = os.path.join(os.path.dirname(__file__), "static")
    settings = {
        'static_path': static_path,
        'debug': config.DEBUG
    }
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/updates", UpdatesHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': static_path}),
    ], **settings)


def run_app():
    app = make_app()
    app.listen(config.WEB_APP_PORT)
    tornado.ioloop.IOLoop.current().start()
