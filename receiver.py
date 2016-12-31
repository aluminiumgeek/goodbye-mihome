from datetime import datetime
import json
import socket
import binascii
import struct
import psycopg2

import config
from plugins import sensor_ht

conn = psycopg2.connect("dbname={} user={} password={}".format(config.DBNAME, config.DBUSER, config.DBPASS))
cursor = conn.cursor()

UDP_IP = config.MIHOME_GATEWAY_IP
UDP_PORT_FROM = 54322
UDP_PORT = 54321
 
MULTICAST_PORT = 9898
SERVER_PORT = 4321
 
MULTICAST_ADDRESS = '224.0.0.50'
SOCKET_BUFSIZE = 1024
 
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
 
sock.bind(("0.0.0.0", MULTICAST_PORT))
 
mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_ADDRESS), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFSIZE)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

current = {}

while True:
    data, addr = sock.recvfrom(SOCKET_BUFSIZE)  # buffer size is 1024 bytes
    print(datetime.now().isoformat(), data)
    message = json.loads(data.decode())
    data = json.loads(message['data'])
    if message.get('model') == 'sensor_ht' and not sensor_ht.process(conn, cursor, current, message, data):
        continue
    current = {}
