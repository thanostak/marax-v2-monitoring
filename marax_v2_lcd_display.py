#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import serial
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
import time
import traceback
from waveshare_OLED import OLED_1in32
from PIL import Image,ImageDraw,ImageFont
logging.basicConfig(level=logging.DEBUG)

try:
    disp = OLED_1in32.OLED_1in32()

    logging.info("\r 1.32inch OLED ")
    # Initialize library.
    disp.Init()
    # Clear display.
    logging.info("clear display")
    disp.clear()
    # Example code stops - my code starts

    is_timer_mode = False
    is_lever_mode = False
    timer_started = False
    time_elapsed = 0
    start_time = time.time()
    stop_time = time.time()
    usb_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    # Change this to True to see Fahrenheit values
    is_fahrenheit = False

    def convert_to_fahrenheit(val):
        return round((val * 9 / 5) + 32, 2)

    def temperature_to_string(val):
        return "{}° F".format(convert_to_fahrenheit(val)) if is_fahrenheit else "{}° C".format(val)

    def draw_stats():
        """
        +1.10 - Software Version
        124 - Current steam temperature in Celsius.
        126 - Target steam temperature in Celsius.
        096 - Current heat exchanger temperature in Celsius.
        0000 - If the machine is fast heating then this will count down until it goes to normal heating mode.
        0 - Heating Element 0 = off, 1 = on.
        0 - Pump Operating 0 = off, 1 = on.
        """
        read_vals = usb_serial.readline().decode('UTF-8').rstrip()
        try:
            individual_vals = read_vals.split(',')
            current_steam_temp = int(individual_vals[1])
            target_steam_temp = int(individual_vals[2])
            current_hx_temp = int(individual_vals[3])
            fast_heating_time_left = int(individual_vals[4])
            is_heating_element_on = int(individual_vals[5])

            line_1 = "T: {}".format(temperature_to_string(current_hx_temp))
            line_2 = "Heating: {}".format("On" if is_heating_element_on else "Off")
            line_3 = "Tgt Steam Temp: {}".format(temperature_to_string(target_steam_temp))
            line_4 = "Steam: {}".format(temperature_to_string(current_steam_temp))
            line_6 = "Fast Heating: {} sec".format(fast_heating_time_left) if fast_heating_time_left else ""
        except IndexError:
            line_2 = ""
            line_3 = ""
            line_4 = ""
            line_5 = ""
            line_6 = ""
        y = top

        #draw.text((5, 2), line_2, font=font, fill="#FFFFFF")
        #draw.text((5, 2), line_3, font=font, fill="#FFFFFF")
        font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 28)
        draw.text((x, y), line_1, font=font, fill = 13)
        y += font.getsize(line_1)[1]
        font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 14)
        draw.text((x, y), line_4, font=font, fill = 13)
        y += font.getsize(line_4)[1]
        draw.text((x, y), line_2, font=font, fill = 13)

    def draw_timer(pump):
        # lol global variables
        global time_elapsed
        global stop_time
        if pump == 1:
            stop_time = time.time()
            time_elapsed = stop_time - start_time
        draw.text((20, 2), str(int(round(time_elapsed, 0))), font=font, fill="#FFFFFF")

    while 1:
        height = disp.height
        width = disp.width

        padding = 20
        top = padding
        bottom = height - padding
        x = 0

        image1 = Image.new('RGB', (height,width), 0)
        draw = ImageDraw.Draw(image1)
        font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
        draw_stats()
        image1 = image1.rotate(90)
        disp.ShowImage(disp.getbuffer(image1))
        # Create blank image for drawing.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        time.sleep(0.2)

    disp.clear()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    disp.module_exit()
    exit()
