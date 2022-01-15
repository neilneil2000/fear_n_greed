#!/usr/bin/env python3
"""Display Fear and Greed Index for Cryptocurrency on 1d RGB pixel graph"""

from time import sleep,time

from typing import Tuple
import colorsys
import ledshim
import requests

import RPi.GPIO as GPIO


class OneDGraph:
    """Representation of OneDimensional Graph with Red->Green Colour gradient using 0-100 as input range"""

    def __init__(self):
        self.graph_value = 0
        self.hue_range = 80
        self.hue_start = 10
        self.max_brightness = 0.8

    def init_leds(self):
        """Initialise LEDs"""
        ledshim.set_clear_on_exit(True)
        ledshim.set_all(r=0, g=0, b=0, brightness=0)
        ledshim.show()

    def calculate_hue(self, value: int) -> int:
        """Calculate hue for given value"""
        hue = (
            (self.hue_start + ((value / float(ledshim.NUM_PIXELS)) * self.hue_range))
            % 360
        ) / 360.0
        return hue

    def convert_hue_to_rgb(self, hue: int) -> Tuple[int, int, int]:
        """Convert hue value to rgb"""
        return (int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0))

    def calculate_brightness(self, value: int) -> int:
        """Calculate Brightness for given value"""
        if value <= 0:
            return 0
        else:
            return min(value, 1.0) * self.max_brightness

    def show_graph(self, graph_value: int) -> None:
        """Display value on graph"""
        self.graph_value = graph_value
        graph_value *= ledshim.NUM_PIXELS / 100
        for pixel_id in range(ledshim.NUM_PIXELS):
            hue = self.calculate_hue(pixel_id)
            red, green, blue = self.convert_hue_to_rgb(hue)
            brightness = self.calculate_brightness(graph_value)
            ledshim.set_pixel(pixel_id, red, green, blue, brightness)
            graph_value -= 1
        ledshim.show()

    def swipe(self, target: int) -> None:
        """Animate graph from current position to target"""
        if target < self.graph_value:
            self.swipe_down(self.graph_value, target)
        else:
            self.swipe_up(self.graph_value, target)

    def swipe_up(self, low: int, high: int) -> None:
        """Animate graph from low to high"""
        for value in range(low + 1, high + 1):
            self.show_graph(value)

    def swipe_down(self, high: int, low: int) -> None:
        """Animate graph from high to low"""
        for value in range(high - 1, low - 1, -1):
            self.show_graph(value)


class DataSource:
    """Data fetcher"""

    url = "https://api.alternative.me/fng/"

    @classmethod
    def get_new_data(cls) -> int:
        """Class Method to fetch updated data"""
        r = requests.get(url=cls.url)
        temp = r.json()["data"].pop()
        fear_n_greed_value = int(temp["value"])
        time_to_next_update = int(temp["time_until_update"])
        print(f"{time()} {temp}")
        return fear_n_greed_value, time_to_next_update


class Button:
    """Button that detects presses and runs callback function"""

    def __init__(self) -> None:
        self.button_id = 0
        self.bounce_time = 0

    def setup(self, button_id: int, bounce_time: int = 300, callback=None) -> None:
        """Setup Button"""
        self.button_id = button_id
        self.bounce_time = bounce_time
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(button_id, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(button_id, GPIO.FALLING, bouncetime=bounce_time)
        GPIO.add_event_callback(button_id, callback)


def main():
    """Daily update of Red-Green Gradient Graph based on Fear N Greed Index"""
    remaining_time = 0
    graph = OneDGraph()
    graph.init_leds()

    graph.swipe(100)

    while True:
        try:
            value, remaining_time = DataSource.get_new_data()
            graph.swipe(value)
        except ConnectionError:
            value = 0
            remaining_time = 60
        remaining_time = min(remaining_time, 3600)  # Ensure we update every day
        remaining_time = max(0, remaining_time) #Avoid weird bug where remaining_time comes back negative
        sleep(remaining_time)


if __name__ == "__main__":
    main()
