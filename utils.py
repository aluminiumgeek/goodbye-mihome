import json
import uuid
from redis import Redis

import config

store = None


def format_value(value, split=False):
    result = str(int(value)/100.0)
    if split:
        return result.split('.')
    return result


def get_store():
    global store
    if store is None:
        store = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
    return store


class Notifications:
    STORE_KEY = 'mihome_notifications'
    store = get_store()

    @staticmethod
    def list():
        stored = Notifications.store.get(Notifications.STORE_KEY)
        return json.loads(stored.decode() if stored else '[]')

    @staticmethod
    def add(type, title, text):
        from web.w import UpdatesHandler

        notifications = Notifications.list()

        id = str(uuid.uuid4())
        notifications.append({
            'uuid': id,
            'type': type,
            'title': title,
            'text': text
        })
        Notifications.store.set(Notifications.STORE_KEY, json.dumps(notifications))

        notifications[-1].update(kind='notification', command='show')
        UpdatesHandler.send_updates(notifications[-1])

        return id

    @staticmethod
    def remove(uuid):
        from web.w import UpdatesHandler

        notifications = Notifications.list()
        for item in notifications[:]:
            if item['uuid'] == uuid:
                notifications.remove(item)
                break
        else:
            return
        Notifications.store.set(Notifications.STORE_KEY, json.dumps(notifications))

        data = {
            'kind': 'notification',
            'command': 'remove',
            'uuid': uuid
        }
        UpdatesHandler.send_updates(data)
