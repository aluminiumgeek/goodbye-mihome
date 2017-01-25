# Yelight Smart Bulb plugin
import json
import re
import socket
import time

from web.w import UpdatesHandler

STORE_KEY = 'yeelight'
YEE_DISCOVER = [
    'M-SEARCH * HTTP/1.1',
    'MAN: "ssdp:discover"',
    'ST: wifi_bulb'
]


def process(store, data):
    data = get_data(data)
    if 'id' not in data:
        return
    add_device(store, data)


def discover(store):
    from mihome import MULTICAST, SOCKET_BUFSIZE

    # Empty stored list
    store.delete(STORE_KEY)

    address, port = MULTICAST.get('yeelight')
    yee_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    yee_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    yee_socket.sendto('\r\n'.join(YEE_DISCOVER).encode(), (address, port))
    
    while True:
        data, _ = yee_socket.recvfrom(SOCKET_BUFSIZE)
        add_device(store, get_data(data.decode()))


def get_devices(store):
    stored = store.get(STORE_KEY)
    return json.loads(stored.decode() if stored else '[]')


def add_device(store, data):
    devices = get_devices(store)
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
