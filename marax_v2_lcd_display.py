#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import serial
import logging
import time
import traceback
import re
from PIL import Image, ImageDraw, ImageFont

picdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "pic"
)
libdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib"
)
if os.path.exists(libdir):
    sys.path.append(libdir)
from waveshare_OLED import OLED_1in32
logging.basicConfig(level=logging.DEBUG)
try:
    disp = OLED_1in32.OLED_1in32()

    logging.info("\r 1.32inch OLED ")
    # Initialize library.
    disp.Init()

    logging.info("clear display")
    disp.clear()
    # Get drawing object to draw on image.
    height = disp.height
    width = disp.width

    padding = 20
    top = padding
    bottom = height - padding
    x = 0
    time_elapsed = 0
    start_time = time.time()
    stop_time = time.time()

    usb_serial = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
    # Change this to True to see Fahrenheit values
    is_fahrenheit = False

    def convert_to_fahrenheit(val):
        return round((val * 9 / 5) + 32, 2)

    def temperature_to_string(val):
        return (
            "{}° F".format(convert_to_fahrenheit(val))
            if is_fahrenheit
            else "{}° C".format(val)
        )

    def validate_input(input):
        # Pattern explanation:
        # \[        - Literal opening bracket
        # '[+]\d+\.\d+' - Single quoted string starting with +, followed by numbers, dot, numbers
        # (?:       - Non-capturing group
        #   ,\s*    - Comma followed by optional whitespace
        #   '\d+'   - Single quoted string of digits
        # ){6}      - Repeat the group exactly 6 times
        # \]        - Literal closing bracket
        pattern = r"\['\+\d+\.\d+',\s*'\d{3}',\s*'\d{3}',\s*'\d{3}',\s*'\d{4}',\s*'\d{1}',\s*'\d{1}'\]"

        if re.match(pattern, input) and re.match(pattern, input).group() == text:
            # Convert string representation of list to actual list
            return eval(input)  # Note: eval() is safe here as we've strictly validated the input
        return None

    def draw_stats(individual_vals):

        """
        +1.10 - Software Version
        124 - Current steam temperature in Celsius.
        126 - Target steam temperature in Celsius.
        096 - Current heat exchanger temperature in Celsius.
        0000 - If the machine is fast heating then this will count down until it goes to normal heating mode.
        0 - Heating Element 0 = off, 1 = on.
        0 - Pump Operating 0 = off, 1 = on.
        """
        print(individual_vals)
        try:
            current_steam_temp = int(individual_vals[1])
            target_steam_temp = int(individual_vals[2])
            current_hx_temp = int(individual_vals[3])
            fast_heating_time_left = int(individual_vals[4])
            is_heating_element_on = int(individual_vals[5])

            line_1 = "T: {}".format(temperature_to_string(current_hx_temp))
            line_2 = "Heating: {}".format("On" if is_heating_element_on else "Off")
            line_3 = "S: {}/{}".format(
                temperature_to_string(current_steam_temp),temperature_to_string(target_steam_temp)
            )
        except IndexError:
            line_2 = ""
            line_3 = ""
        y = top

        font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 24)
        draw.text((x, y), line_1, font=font, fill=13)
        y += font.getsize(line_1)[1]
        font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 15)
        draw.text((x, y), line_2, font=font, fill=13)
        y += font.getsize(line_2)[1]
        draw.text((x, y), line_3, font=font, fill=13)

    while 1:
        image1 = Image.new('L', (height, width), 0)
        draw = ImageDraw.Draw(image1)
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        height = disp.height
        width = disp.width

        padding = 20
        top = padding
        bottom = height - padding
        x = 0
        read_vals = usb_serial.readline().decode("UTF-8").rstrip()
        individual_vals = read_vals.split(",")
        is_pump_on = int(individual_vals[6])
        if is_pump_on == 0:
            draw_stats(individual_vals)
            time_elapsed = 0
            start_time = None
        else:
            if start_time is None:
                start_time = time.time()
            print("Doulevei i trompa")
            time_elapsed = time.time() - start_time

            font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 76)
            y = top
            line_t = "{}s".format(time_elapsed)
            draw.text((x, y), line_t, font=font, fill=13)

        image1 = image1.rotate(270)
        disp.ShowImage(disp.getbuffer(image1))

        time.sleep(0.1)


except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    disp.module_exit()
    exit()
