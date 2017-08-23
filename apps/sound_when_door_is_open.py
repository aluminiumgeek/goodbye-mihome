import json

from plugins import gateway_speaker
from plugins.magnet import MAGNET_STORE_KEY

DOOR_SENSOR_SID = '158d0001837ec2'


def run(store, conn, cursor):
    """Play sound on the Gateway when somebody opens the door"""
    p = store.pubsub(ignore_subscribe_messages=True)
    p.subscribe(MAGNET_STORE_KEY)

    for message in p.listen():
        if message.get('type') != 'message':
            continue

        data = json.loads(message.get('data').decode())
        if data.get('sid') == DOOR_SENSOR_SID and data.get('status') == 'open':
            gateway_speaker.play(3)  # Standard alarm sound
