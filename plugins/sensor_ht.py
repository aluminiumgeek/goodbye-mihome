from datetime import datetime


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

    query = "INSERT INTO ht(sid, temperature, humidity, dt) VALUES ('{}', {}, {}, '{}')".format(message['sid'], current['temperature'], current['humidity'], datetime.now().isoformat())
    cursor.execute(query)
    conn.commit()
    return True
