import time

from plugins import gateway_led


def run(store, conn, cursor):
    """Blink gateway LED with 400ms interval"""
    while True:
        gateway_led.toggle()
        time.sleep(0.4)
