from mihome import get_key, send_command
from utils import get_store


def get_base_command():
    store = get_store()
    return {
        'cmd': 'write',
        'model': 'gateway',
        'sid': store.get('gateway_sid').decode(),
        'short_id': 0,
        'data': {
            'key': get_key().decode()
        }
    }


def play(sound_id, volume=20):
    """
    sound_id: 0-8, 10, 13, 20-29 - standard ringtones; >= 10001 - user-defined ringtones uploaded to your gateway via MiHome app.
    volume: level from 1 to 100.

    Check the reference to get more about sound_id value: https://github.com/louisZL/lumi-gateway-local-api/blob/master/%E7%BD%91%E5%85%B3.md
    """
    command = get_base_command()
    command['data'].update(mid=sound_id, vol=volume)
    send_command(command)


def stop():
    command = get_base_command()
    command['data'].update(mid=10000)
    send_command(command)
