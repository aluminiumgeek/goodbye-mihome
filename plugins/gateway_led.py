import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mihome import get_key, send_command
from utils import get_store

DEVICE = 'gateway_led'
STORE_KEY = 'gateway_led_value'
store = get_store()


def get_base_command():
    command = {
        'cmd': 'write',
        'model': 'gateway',
        'sid': store.get('gateway_sid').decode(),
        'data': {
            'rgb': None,
            'key': get_key().decode()
        }
    }
    return command


def get_status():
    """Returns brigthness (hex), color (hex), status (on/off)"""
    value = store.get(STORE_KEY) or '33ff4455'
    return value[:2].decode(), value[2:].decode(), not store.get(STORE_KEY + 'off')


def set_color(code):
    value = store.get(STORE_KEY) or '0'
    if len(value) > 1:
        brightness = value[:2]
    rgb = brightness.decode() + code
    set_rgb(rgb)


def set_brightness(level):
    value = store.get(STORE_KEY) or '0'
    if len(value) > 1:
        color = value[2:]
    rgb = level + color.decode()
    set_rgb(rgb)


def set_rgb(rgb, send=True):
    brightness, color = rgb[:2], rgb[2:]
    if int(brightness, 16) > 100:
        brightness = '64'
    rgb = brightness + color
    store.set(STORE_KEY, rgb)
    if not send or is_blocked():
        return
    store.delete(STORE_KEY + 'off')
    command = get_base_command()
    command['data']['rgb'] = int(rgb, 16)
    send_command(command)


def toggle():
    command = get_base_command()
    if store.get(STORE_KEY + 'off'):
        store.delete(STORE_KEY + 'off')
        rgb = store.get(STORE_KEY) or '99ffffff'
        command['data']['rgb'] = int(rgb, 16)
    else:
        store.set(STORE_KEY + 'off', 1)
        command['data']['rgb'] = 0
    send_command(command)


def block():
    """Prevent LED from changing"""
    store.set(STORE_KEY + 'block', 1)


def unblock():
    """Release block"""
    store.delete(STORE_KEY + 'block')


def is_blocked():
    return store.get(STORE_KEY + 'block')
