import json
import time
from threading import Thread
from pyquery import PyQuery as pq

from plugins import gateway_led
from utils import Notifications

STORE_KEY = 'energo_pro_outage'
BLINKING_STORE_KEY = 'energo_pro_outage_blinking'
NOTIFICATION_TITLE = 'Electricity outage'
AREA = 'batumi'


def run(store, conn, cursor):
    url = 'http://www.energo-pro.ge/category/electricity-suspensions/'

    # Reset stored values if needed / restore blinking after restart 
    if is_notification_shown():
        store.delete(BLINKING_STORE_KEY)
        if gateway_led.is_blocked():
            gateway_led.unblock()
    else:
        Thread(target=blink, args=(store,)).start()
        store.set(BLINKING_STORE_KEY, 1)

    while True:
        try:
            page = pq(url)
        except:  # it will be a connection error or something like that anyway
            sleep(10)
            continue
        if AREA in str(page).lower():
            for el in page('.susp-table .bwm-post.post').items():
                region, location, customers, date, time_from, time_to = [el('div').eq(i).text() for i in range(6)]

                if AREA in region.lower() or AREA in location.lower():
                    if not add_to_parsed(store, el.text()):
                        continue
                    text = '<b>Location</b>: {}, {}<br/><b>When</b>: {}, from {} to {}<br/>'.format(region, location, date, time_from, time_to)
                    if not is_notification_exists(text):
                        Notifications.add('error', NOTIFICATION_TITLE, text)

                    if not store.get(BLINKING_STORE_KEY):
                        Thread(target=blink, args=(store,)).start()
                        store.set(BLINKING_STORE_KEY, 1)

        sleep()


def sleep(delay=60 * 60):
    time.sleep(delay)


def add_to_parsed(store, info):
    """
    Save power outage info.
    Returns True if info added; False if this info already stored
    """
    stored = store.get(STORE_KEY)
    parsed = json.loads(stored.decode() if stored else '[]')
    if info in parsed:
        return False
    parsed.append(info)
    store.set(STORE_KEY, json.dumps(parsed))
    return True


def is_notification_exists(text):
    for item in Notifications.list():
        if item['text'] == text:
            return True
    return False


def is_notification_shown():
    for item in Notifications.list():
        if item['title'] == NOTIFICATION_TITLE:
            return False
    return True


def blink(store):
    gateway_led.block()

    check_time = time.time()
    brightness_before, color_before, _ = gateway_led.get_status()
    while True:
        if time.time() - check_time > 2:
            if is_notification_shown():
                break
            check_time = time.time()

        gateway_led.set_rgb('55FF0000', False)
        gateway_led.toggle()
        sleep(1)

    # Stop blinking, release LED and set previous brightness and color
    gateway_led.unblock()
    argb = brightness_before + color_before
    gateway_led.set_rgb(argb if argb != '55FF0000' else '5500FF00')
    store.delete(BLINKING_STORE_KEY)
