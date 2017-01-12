import random
import time

from plugins import gateway_led

COLORS = ['FF5733', 'FFC300', 'FF5733', 'C70039', '581845', '008000', '00FFFF', '008080', '0000FF', 'F5CBA7', 'AEB6BF', 'CACFD2', 'A569BD', '8E44AD']


def run(store, conn, cursor):
    """Set random LED color every 10 seconds"""
    while True:
        gateway_led.set_color(random.choice(COLORS))
        time.sleep(0.4)
