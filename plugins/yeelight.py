# Yelight Smart Bulb plugin
# Specification: http://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf
#
# Supported commands: toggle, set_power, set_bright, start_cf, stop_cf, set_scene,
# cron_add, cron_get, cron_del, set_adjust, set_name.
#
# Unsupported (feel free to implement something of this): set_ct_abx, set_rgb,
# set_hsv, set_music.

import json
import re
import socket
import time

from web.w import UpdatesHandler
from utils import get_store

STORE_KEY = 'yeelight'
DEVICE = 'yeelight'
YEE_DISCOVER = [
    'M-SEARCH * HTTP/1.1',
    'MAN: "ssdp:discover"',
    'ST: wifi_bulb'
]
store = get_store()


def toggle(device_id=None):
    """
    Toggle the smart LED.
    """
    return send_command({
        'method': 'toggle',
        'params': []
    }, device_id)


def set_power(power, effect='smooth', duration=500, device_id=None):
    """
    Switch on or off the smart LED.
    `power` - Boolean
    `effect` - "smooth" or "sudden"
    `duration` - duration of smooth effect, ignored if effect is "sudden"
    """
    return send_command({
        'method': 'set_power',
        'params': ['on' if power else 'off', effect, duration]
    }, device_id)


def set_bright(brightness, effect='smooth', duration=500, device_id=None):
    """
    Change the brightness of a smart LED.
    `brightness` - integer from 1 to 100
    """
    return send_command({
        'method': 'set_bright',
        'params': [brightness, effect, duration]
    }, device_id)


def start_cf(flow_expression, count=1, action=0, device_id=None):
    """
    Start a color flow (series of smart LED visible state changes; see the Yeelight specification for details).
    `flow_expression` - list of tuples contains 4 elements (duration, mode, value, brightness). Example: [(1000, 2, 2700, 100), (500, 1, 255, 10)]. Again, see the specification for details.
    `count` - how many times perform flow expression (0 - loop forever)
    `action` - action taken after the flow is stopped (0 - recover to the state before; 1 - stay where the flow is stopped; 2 - turn off smart LED)
    """
    return send_command({
        'method': 'start_cf',
        'params': [count, action, ', '.join([', '.join(map(str, x)) for x in flow_expression])]
    }, device_id)


def stop_cf(device_id=None):
    """
    Stop a running color flow.
    """
    return send_command({
        'method': 'stop_cf',
        'params': []
    }, device_id)


def set_scene(state_type, *args, device_id=None):
    """
    Set the smart LED directly to specified state. See the specification for details.
    `state_type` - color|hsv|ct|cf|auto_delay_off
    `*args` - state type specific parameters
    """
    return send_command({
        'method': 'set_scene',
        'params': [state_type] + list(args)
    }, device_id)


def cron_add(state_type, value, device_id=None):
    """
    Start a time job on the smart LED.
    `state_type` - currently can only be 0 (means power off)
    `value` - length of the timer (minutes)
    """
    return send_command({
        'method': 'cron_add',
        'params': [state_type, value]
    }, device_id)


def cron_get(state_type, device_id=None):
    """
    Retrieve current cron jobs of the specified type.
    """
    return send_command({
        'method': 'cron_get',
        'params': [state_type]
    }, device_id)


def cron_del(state_type, device_id=None):
    """
    Stop the specified cron job.
    """
    return send_command({
        'method': 'cron_del',
        'params': [state_type]
    }, device_id)


def set_adjust(action, prop, device_id=None):
    """
    Adjust brightness, color temperature or color.
    `action` - increase|decrease|circle
    `prop` - property to adjust: bright|ct|color
    """
    return send_command({
        'method': 'set_adjust',
        'params': [action, prop]
    }, device_id)


def set_name(name, device_id=None):
    """
    Set name for a smart LED.
    """
    return send_command({
        'method': 'set_name',
        'params': [name]
    }, device_id)


def process(data):
    data = get_data(data)
    if 'id' not in data:
        return
    add_device(data)


def discover():
    from mihome import MULTICAST, SOCKET_BUFSIZE

    # Empty stored list
    store.delete(STORE_KEY)

    address, port = MULTICAST.get('yeelight')
    yee_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    yee_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    yee_socket.sendto('\r\n'.join(YEE_DISCOVER).encode(), (address, port))
    
    while True:
        data, _ = yee_socket.recvfrom(SOCKET_BUFSIZE)
        print(data)
        add_device(get_data(data.decode()))


def get_devices():
    stored = store.get(STORE_KEY)
    return json.loads(stored.decode() if stored else '[]')


def add_device(data):
    devices = get_devices()
    for i, device in enumerate(devices[:]):
        if device['id'] == data['id']:
            devices.pop(i)
    devices.append(data)
    store.set(STORE_KEY, json.dumps(devices))


def get_data(data):
    data = dict(re.findall(r'(\w+):(.*)', data.replace('\r', '')))
    for key in data:
        data[key] = data[key].strip()
    return data


def send_command(command, device_id=None):
    """
    Send command to a bulb. If no bulb id specified, send command to all smart LED bulbs
    """
    devices = get_devices()
    if device_id is not None:
        devices = filter(lambda x: x['id'] == device_id, devices)
    results = []
    for device in devices:
        command.update(id=device['id'])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        address, port = device['Location'].replace('yeelight://', '').split(':')
        s.connect((address, int(port)))
        s.send(json.dumps(command).encode('ascii') + b'\r\n')
        data = {}
        if command.get('method') in ['set_name']:
            messages_count = 1
        else:
            messages_count = 2
        for _ in range(messages_count):  # bulb returns two messages: status and props
            data.update(json.loads(s.recv(1024).decode()))
        s.close()
        data.update(id=device['id'])
        results.append(data)

    return results
