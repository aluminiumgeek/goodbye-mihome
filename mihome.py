import binascii
import code
import importlib
import json
import psycopg2
import readline
import socket
import struct
import sys
import time
from Crypto.Cipher import AES
from datetime import datetime
from threading import Thread

import config
from plugins import sensor_ht, gateway, yeelight
from utils import get_store
from web.w import run_app as web_app

conn = psycopg2.connect("dbname={} user={} password={}".format(config.DBNAME, config.DBUSER, config.DBPASS))
cursor = conn.cursor()

MULTICAST = {
    'mihome': ('224.0.0.50', 9898),
    'yeelight': ('239.255.255.250', 1982)
}
SOCKET_BUFSIZE = 1024

IV = bytes([0x17, 0x99, 0x6d, 0x09, 0x3d, 0x28, 0xdd, 0xb3, 0xba, 0x69, 0x5a, 0x2e, 0x6f, 0x58, 0x56, 0x2e])


def receiver(service='mihome'):
    assert service in MULTICAST, 'No such service'
    store = get_store()
    address, port = MULTICAST.get(service)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
 
    mreq = struct.pack("=4sl", socket.inet_aton(address), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFSIZE)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    current = {}

    while True:
        data, _ = sock.recvfrom(SOCKET_BUFSIZE)  # buffer size is 1024 bytes
        print(datetime.now().isoformat(), data)
        if service == 'mihome':
            message = json.loads(data.decode())
            data = json.loads(message['data'])
            if message.get('model') == 'sensor_ht' and not sensor_ht.process(conn, cursor, current, message, data):
                continue
            elif message.get('model') == 'gateway':
                gateway.process(store, message, data)
            current = {}
        elif service == 'yeelight':
            yeelight.process(data.decode())


def send_command(command, timeout=10):
    _, port = MULTICAST.get('mihome')
    if isinstance(command.get('data'), dict):
        command['data'] = json.dumps(command['data'])
    address = get_store().get('gateway_addr')
    if address is None:
        print("Doesn't receive any heartbeat from gateway. Delaying request for 10 seconds.")
        time.sleep(10)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    sock.connect((address, port))
    sock.send(json.dumps(command).encode('ascii'))
    data = None
    try:
        data, addr = sock.recvfrom(SOCKET_BUFSIZE)
    except ConnectionRefusedError:
        print("send_command :: recvfrom() connection refused: {}:{}".format(address.decode(), port))
    except socket.timeout:
        print("send_command :: recvfrom() timed out: {}:{}".format(address.decode(), port))
    finally:
        sock.close()
    return data


def get_key():
    """Get current gateway key"""
    cipher = AES.new(config.MIHOME_GATEWAY_PASSWORD, AES.MODE_CBC, IV)
    encrypted = cipher.encrypt(get_store().get('gateway_token'))
    return binascii.hexlify(encrypted)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'shell':
        vars = globals().copy()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()
        sys.exit()

    Thread(target=web_app).start()

    for app_name in config.ENABLED_APPS:
        try:
            app = importlib.import_module('apps.{}'.format(app_name))
        except ImportError as e:
            print('Could not import app "{}": {}'.format(app_name, e))
            continue
        kwargs = {'store': get_store(), 'conn': conn, 'cursor': cursor}
        Thread(target=app.run, kwargs=kwargs).start()
        print('Loaded app: {}'.format(app_name))

    for service in MULTICAST:
        Thread(target=receiver, args=(service,)).start()

    # Discover Yeelight bulbs
    yeelight.discover()
