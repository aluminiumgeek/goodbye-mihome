import datetime
import time

from plugins import gateway_led
from utils import time_in_range

# [start_time, end_time]
EVENING = [datetime.time(18, 30), datetime.time(8, 30)]

# [normal_brightness, dim_brightness]; possible values: from 0 to 100
BRIGHTNESS = [28, 3]


def run(store, conn, cursor):
    """Dim gateway LED in the evening hours"""
    start_time, end_time = EVENING
    normal_brightness, dim_brightness = map(lambda x: hex(x)[2:], BRIGHTNESS)
    dimmed = None
    while True:
        is_evening = time_in_range(start_time, end_time, datetime.datetime.now().time())
        if is_evening and not dimmed:
            gateway_led.set_brightness(dim_brightness)
            dimmed = True
        elif dimmed is True or dimmed is None:
            gateway_led.set_brightness(normal_brightness)
            dimmed = False
        time.sleep(4)
