#!/usr/bin/env python3
"""Display Fear and Greed Index for Cryptocurrency on 1d RGB pixel graph"""

import colorsys
import datetime
from time import sleep
from typing import Tuple

import gpiozero
import ledshim
import requests


class OneDGraph:
    """
    Representation of OneDimensional Graph with Red->Green Colour gradient
    Uses 0-100 as input range
    LED[0] on from 1 onwards
    """

    def __init__(self, max_value: int = 100) -> None:
        if max_value:
            self.max_value = max_value
        self.scale_factor = ledshim.NUM_PIXELS / self.max_value

        self.graph_target = 0
        self.graph_value = 0
        self.hue_range = 80
        self.hue_start = 10
        self.max_brightness = 0.8
        self.leds_on = False
        self.pixel_colours = []

    def init_leds(self):
        """Initialise LEDs"""
        ledshim.set_clear_on_exit(True)
        ledshim.set_all(r=0, g=0, b=0, brightness=0)
        ledshim.show()
        self.leds_on = True
        self.compute_colours()

    def compute_colours(self):
        """Compute Colours for each pixel"""
        for pixel_id in range(ledshim.NUM_PIXELS):
            hue = self.calculate_hue(pixel_id)
            red, green, blue = self.convert_hue_to_rgb(hue)
            self.pixel_colours.append((red, green, blue))

    def calculate_hue(self, value: int) -> int:
        """Calculate hue for given value"""
        hue = (
            (self.hue_start + ((value / float(ledshim.NUM_PIXELS)) * self.hue_range))
            % 360
        ) / 360.0
        return hue

    @staticmethod
    def convert_hue_to_rgb(hue: int) -> Tuple[int, int, int]:
        """Convert hue value to rgb"""
        return (int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0))

    def show_graph(self, graph_value: int) -> None:
        """Display value on graph"""
        self.graph_value = graph_value
        pixel_value = graph_value * self.scale_factor
        for pixel_id in range(ledshim.NUM_PIXELS):
            brightness = self.max_brightness if pixel_id < pixel_value else 0
            red, green, blue = self.pixel_colours[pixel_id]
            ledshim.set_pixel(pixel_id, red, green, blue, brightness)
        ledshim.show()

    def swipe(self, target: int = None) -> None:
        """Animate graph from current position to {target}"""
        if target is None:
            target = self.graph_value
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

    def toggle_lights(self) -> None:
        """Switch state from lights on to off or vice versa, using swipe"""
        if self.leds_on:
            self.graph_target = self.graph_value
            self.swipe(0)
            self.leds_on = False
        else:
            self.swipe(self.graph_target)
            self.leds_on = True


class DataSource:
    """Data fetcher"""

    url = "https://api.alternative.me/fng/"

    @classmethod
    def get_new_data(cls) -> int:
        """Class Method to fetch updated data"""
        response = requests.get(url=cls.url)
        temp = response.json()["data"].pop()
        fear_n_greed_value = int(temp["value"])
        time_to_next_update = int(temp["time_until_update"])
        return fear_n_greed_value, time_to_next_update


class Button:
    """Button that detects presses and runs callback function"""

    def __init__(self) -> None:
        self.button_id = 0
        self.bounce_time = 0
        self.button: gpiozero.Button = None

    def setup(self, button_id: int, bounce_time: float = 0.2, callback=None) -> None:
        """Setup Button"""
        self.button_id = button_id
        self.bounce_time = bounce_time
        self.button = gpiozero.Button(pin=button_id, bounce_time=bounce_time)
        self.button.when_pressed = callback


def main():
    """Daily update of Red-Green Gradient Graph based on Fear N Greed Index"""
    remaining_time = 0
    graph = OneDGraph()
    graph.init_leds()
    led_button = Button()
    led_button.setup(27, callback=graph.toggle_lights)
    graph.swipe(100)

    while True:
        try:
            value, remaining_time = DataSource.get_new_data()
        except requests.ConnectionError as e:
            print(f"{str(datetime.datetime.now())} CONNECTION ERROR")
            print(f"{e}")
            value = 0
            remaining_time = 60
        else:
            graph.graph_target = value
            graph.swipe(value)

        remaining_time = min(remaining_time, 3600)  # Ensure we update every day
        remaining_time = max(30, remaining_time)  # Handle negatives
        sleep(remaining_time)


if __name__ == "__main__":
    main()
