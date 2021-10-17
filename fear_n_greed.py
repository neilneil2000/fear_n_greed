#!/usr/bin/env python3

from time import sleep
from sys import exit

import colorsys
import ledshim
import requests

import RPi.GPIO as GPIO

url = 'https://api.alternative.me/fng/'

fng = 0
graph_value = 0

ledshim.set_clear_on_exit(True)

hue_range = 80
hue_start = 10
max_brightness = 0.8
brightness = 0.6

def callback_27(channel):
    global on_off
    if (graph_value>0):
        swipe(0)
    else:
        swipe(fng)

def init_leds():
    ledshim.set_all(0,0,0,0)
    ledshim.show()

def update_index():
    global fng
    global delay
    global graph_value
    try:
        r = requests.get(url=url)
        temp = r.json()['data'].pop()
        fng = int(temp['value'])
        delay = int(temp['time_until_update'])
        #print('Index = ' + str(fng))
    except (requests.ConnectionError, requests.ConnectTimeout):
        print('Connection Error')

def show_graph(v):
    global graph_value
    graph_value = v
    v *= ledshim.NUM_PIXELS/100
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

def swipe(target):
    global graph_value
    #print(str(graph_value) + 'before swipe')
    if target<graph_value:
        swipe_down(graph_value, target)
    else:
        swipe_up(graph_value, target)
    #print(str(graph_value) + 'after swipe')


def swipe_up(low, high):
    for x in range(low+1, high+1):
        show_graph(x)

def swipe_down(high, low):
    for x in range(high-1, low-1, -1):
        show_graph(x)



#Set Up On_Off Button
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(27, GPIO.FALLING, bouncetime=300)
GPIO.add_event_callback(27, callback_27)

init_leds()

update_index()
swipe(100)
swipe(fng)

while 1:
    delay = min(delay,86460) #Ensure we update every day
    #print('Delaying for ' + str(delay) + ' seconds')
    sleep(delay)
    update_index()
    swipe(fng)

