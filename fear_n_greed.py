#!/usr/bin/env python

from time import sleep
from sys import exit

import colorsys
import ledshim
import requests

import RPi.GPIO as GPIO

url = 'https://api.alternative.me/fng/'

fng = 0

ledshim.set_clear_on_exit(False)

hue_range = 80
hue_start = 10
max_brightness = 0.8
brightness = 0.6

on_off = brightness

def callback_27(channel):
    global on_off
    print('Button 27 Pressed')
    if (on_off>0):
        on_off = 0
    else:
        on_off = brightness
    ledshim.set_brightness(on_off)
    ledshim.show()

GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(27, GPIO.FALLING, bouncetime=200)
GPIO.add_event_callback(27, callback_27)



def update_index():
    global fng
    global delay
    try:
        r = requests.get(url=url)
        temp = r.json()['data'].pop()
        fng = int(temp['value'])
        delay = int(temp['time_until_update'])
        print('Index = ' + str(fng))
    except (requests.ConnectionError, requests.ConnectTimeout):
        print('Connection Error')

def show_graph(v, r, g, b):
    v *= ledshim.NUM_PIXELS
    for x in range(ledshim.NUM_PIXELS):
        hue = ((hue_start + ((x / float(ledshim.NUM_PIXELS)) * hue_range)) % 360) / 360.0
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
        if v < 0:
            brightness = 0
        else:
            brightness = min(v, 1.0) * max_brightness

        ledshim.set_pixel(x, r, g, b, brightness)
        v -= 1

    ledshim.show()

ledshim.set_brightness(brightness)

while 1:
    update_index()

    for x in range(100):
        v = x/100
        show_graph(v, 255, 0, 255)
    for x in range(100-fng):
        v = x/100
        show_graph(1-v, 255, 0, 255)

    update_index()
    #show_graph(fng/100, 255, 0, 255)
    delay = min(delay,86460) #Ensure we update every day
    print('Delaying for ' + str(delay) + ' seconds')
    sleep(delay)
