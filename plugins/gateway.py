from plugins.gateway_led import STORE_KEY as LED_STORE_KEY
from web.w import UpdatesHandler


def process(store, message, data):
    """
    Track gateway token that changes every 10 seconds.
    Track "report" commands from gateway internal devices (like LED)
    """
    if message.get('model') != 'gateway':
        return
    cmd = message.get('cmd')
    sid = message.get('sid')
    if cmd == 'heartbeat':
        store.set('gateway_sid', sid)
        store.set('gateway_token', message.get('token'))
        store.set('gateway_addr', data.get('ip'))
    elif cmd == 'report':
        if data.get('rgb') is not None:
            push_data = {
                'device': 'gateway_led',
                'sid': sid
            }
            rgb = data.get('rgb')
            if rgb == 0:
                store.set(LED_STORE_KEY + 'off', 1)
                push_data.update(status='off')
            else:
                store.delete(LED_STORE_KEY + 'off')
                hex_rgb = hex(data.get('rgb'))[2:]
                if len(hex_rgb) == 7:
                    hex_rgb = '0' + hex_rgb
                store.set(LED_STORE_KEY, hex_rgb)
                push_data.update(brightness=hex_rgb[:2], color=hex_rgb[2:])

            UpdatesHandler.send_updates(push_data)
