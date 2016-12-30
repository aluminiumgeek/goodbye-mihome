import os
import random
import sys

import psycopg2
import tornado.ioloop
import tornado.web

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config

conn = psycopg2.connect("dbname={} user={} password={}".format(config.DBNAME, config.DBUSER, config.DBPASS))


def get_cursor():
    global conn
    return conn.cursor()


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        cursor = get_cursor()
        cursor.execute('SELECT DISTINCT ON (sid) sid, temperature, humidity FROM ht ORDER BY sid, dt DESC')
        sensors = []
        for sid, temperature, humidity in cursor.fetchall():
            sensors.append({
                'name': config.SENSORS.get(sid, sid),
                'temperature': str(temperature/100.0).split('.'),  #'{:0.2f}'.format(temperature/100.0),
                'humidity': str(humidity/100.0).split('.')  #'{:0.2f}'.format(humidity/100.0)
            })

        bg_files = os.listdir(os.path.join(os.path.dirname(__file__), "static", "img", "bg"))
        bg_files = list(filter(lambda x: x.endswith('.jpg'), bg_files))

        self.render("templates/index.html", sensors=sensors, images=bg_files)


def make_app():
    static_path = os.path.join(os.path.dirname(__file__), "static")
    settings = {
        'static_path': static_path,
        'debug': config.DEBUG
    }
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': static_path}),
    ], **settings)


if __name__ == "__main__":
    app = make_app()
    app.listen(config.WEB_APP_PORT)
    tornado.ioloop.IOLoop.current().start()
