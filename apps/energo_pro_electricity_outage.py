import time
from threading import Thread
from pyquery import PyQuery as pq

from plugins import gateway_led
from utils import Notifications

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
            sleep()
        if AREA in str(page).lower():
            for el in page('.susp-table .bwm-post.post').items():
                region, location, customers, date, time_from, time_to = [el('div').eq(i).text() for i in range(6)]
                if AREA in region.lower() or AREA in location.lower():
                    text = '<b>Location</b>: {}, {}<br/><b>When</b>: {}, from {} to {}<br/>'.format(region, location, date, time_from, time_to)
                    if not is_notification_exists(text):
                        Notifications.add('error', NOTIFICATION_TITLE, text)

                    if not store.get(BLINKING_STORE_KEY):
                        Thread(target=blink, args=(store,)).start()
                        store.set(BLINKING_STORE_KEY, 1)

        sleep()


def sleep():
    time.sleep(60 * 60) # once an hour


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

        gateway_led.set_rgb('FFFF0000', False)
        gateway_led.toggle()
        time.sleep(1)

    # Stop blinking, release LED and set previous brightness and color
    gateway_led.unblock()
    argb = brightness_before + color_before
    gateway_led.set_rgb(argb if argb != 'FFFF0000' else '5500FF00')
    store.delete(BLINKING_STORE_KEY)
