import json

import config
from utils import Notifications
from web.w import UpdatesHandler

MAGNET_STORE_KEY = 'magnet'
LOW_BATTERY_VOLTAGE = 2800


def process(store, message, data):
    if message.get('model') != 'magnet':
        return

    sid = message.get('sid')

    if data.get('status'):
        # Publishing event using redis PubSub feature. Anyone could subscribe to the channel
        # and get live updates like:
        # p = store.pubsub()
        # p.subscribe(MAGNET_STORE_KEY)
        # print(p.get_message())
        #
        # See the `sound_when_door_is_open` app from `apps` dir for example usage
        update = {
            'device': 'magnet',
            'sid': sid,
            'name': config.SENSORS.get(sid, {}).get('name', sid),
            'status': data.get('status')
        }
        store.publish(MAGNET_STORE_KEY, json.dumps(update))
        store.set('{}_{}'.format(MAGNET_STORE_KEY, sid), data.get('status'))

        # Send update to web
        UpdatesHandler.send_updates(update)

    elif data.get('voltage'):
        if int(data.get('voltage')) <= LOW_BATTERY_VOLTAGE:
            Notifications.add('warning', 'Low battery', 'Low battery on magnet {}'.format(config.SENSORS.get(sid, {}).get('name', sid)))
