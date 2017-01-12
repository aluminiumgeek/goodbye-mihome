import binascii
import json
import psycopg2
import socket
import struct
import time
from Crypto.Cipher import AES
from datetime import datetime
from threading import Thread
from redis import StrictRedis

import config
from plugins import sensor_ht, gateway_token
from web.w import run_app

conn = psycopg2.connect("dbname={} user={} password={}".format(config.DBNAME, config.DBUSER, config.DBPASS))
cursor = conn.cursor()
store = StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
 
MULTICAST_PORT = 9898
 
MULTICAST_ADDRESS = '224.0.0.50'
SOCKET_BUFSIZE = 1024

IV = bytes([0x17, 0x99, 0x6d, 0x09, 0x3d, 0x28, 0xdd, 0xb3, 0xba, 0x69, 0x5a, 0x2e, 0x6f, 0x58, 0x56, 0x2e])
CIPHER = AES.new(config.MIHOME_GATEWAY_PASSWORD, AES.MODE_CBC, IV)


def receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", MULTICAST_PORT))
 
    mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_ADDRESS), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFSIZE)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    current = {}

    while True:
        data, (addr, _) = sock.recvfrom(SOCKET_BUFSIZE)  # buffer size is 1024 bytes
        store.set('gateway_addr', addr)
        print(datetime.now().isoformat(), data)
        message = json.loads(data.decode())
        data = json.loads(message['data'])
        if message.get('model') == 'sensor_ht' and not sensor_ht.process(conn, cursor, current, message, data):
            continue
        elif message.get('model') == 'gateway':
            result = gateway_token.process(message)
            if not result:
                continue
            sid, token = result
            store.set('gateway_sid', sid)
            store.set('gateway_token', token)
            continue
        current = {}


def send_command(command):
    gateway_addr = store.get('gateway_addr')
    if gateway_addr is None:
        print("Doesn't receive any heartbeat from gateway. Delaying request for 10 seconds.")
        time.sleep(10)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((gateway_addr, MULTICAST_PORT))
    sock.send(json.dumps(command).encode('ascii'))
    data, addr = sock.recvfrom(SOCKET_BUFSIZE)
    sock.close()
    return data


def get_key():
    """Get current gateway key"""
    encrypted = CIPHER.encrypt(store.get('gateway_token'))
    return binascii.hexlify(encrypted)


if __name__ == '__main__':
    Thread(target=run_app).start()
    receiver()
