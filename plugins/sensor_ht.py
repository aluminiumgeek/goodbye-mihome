import json
from datetime import datetime

from web.w import UpdatesHandler
from web.utils import format_value


def process(conn, cursor, current, message, data):
    if message.get('model') != 'sensor_ht':
        return False
    
    save = False
    if message.get('cmd') == 'report':
        if current:
            save = True
        if 'temperature' in data:
            current['temperature'] = data['temperature']
        if 'humidity' in data:
            current['humidity'] = data['humidity']
    else:
        current = data
    if not save:
        return False

    query = "INSERT INTO ht(sid, temperature, humidity, dt) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (message['sid'], current['temperature'], current['humidity'], datetime.now().isoformat()))
    conn.commit()

    data = {
        'device': 'sensor_ht',
        'sid': message['sid'],
        'temperature': format_value(current['temperature']),
        'humidity': format_value(current['humidity'])
    }
    UpdatesHandler.send_updates(data)

    return True
