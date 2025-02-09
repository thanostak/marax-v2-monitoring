#!/usr/bin/python3
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

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Logging setup

ch = logging.FileHandler("/home/pi/marax-display/log_marax_display.log")
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

disp = OLED_1in32.OLED_1in32()

logging.info("\r 1.32inch OLED ")
# Initialize library.
disp.Init()

logging.info("clear display")
disp.clear()
# Get drawing object to draw on image.
height = disp.height
width = disp.width
#draw.rectangle((0, 0, width, height), outline=0, fill=0)
#rotated = image.rotate(rotation)
#disp.ShowImage(disp.getbuffer(rotated))

padding = 20
top = padding
bottom = height - padding
x = 0
time_elapsed = 0
start_time = time.time()
stop_time = time.time()
machine_on = 0
is_pump_on = None

usb_serial = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)


def temperature_to_string(val):
    return "{}° C".format(val)


def validate_input(input: list) -> bool:
    """Validates string matches pattern like: '+1.10', '117', '112', '095'"""
    pattern = r'^\+1\.10$'
    if input is not None:
        first_value = input.split(",")[0]
        if re.match(pattern, first_value):
            return True
    else:
        return False


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
    try:
        individual_vals = read_vals.split(',')
        current_steam_temp = int(individual_vals[1])
        target_steam_temp = int(individual_vals[2])
        current_hx_temp = int(individual_vals[3])
        is_heating_element_on = int(individual_vals[5])

        line_1 = "T: {}".format(temperature_to_string(current_hx_temp))
        line_2 = "Heating: {}".format("On" if is_heating_element_on else "Off")
        line_3 = "S: {}/{}".format(
            temperature_to_string(current_steam_temp),temperature_to_string(target_steam_temp)
        )
    except IndexError:
        line_1 = ""
        line_2 = ""
        line_3 = ""

    y = top
    font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 24)
    draw.text((x, y), line_1, font=font, fill=13)
    y += font.getsize(line_1)[1]
    font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 15)
    draw.text((x, y), line_2, font=font, fill=13)
    y += font.getsize(line_2)[1]
    draw.text((x, y), line_3, font=font, fill=10)


def read_serial_safely(usb_serial):
    try:
        data = usb_serial.readline()
        if not data:
            logging.warning("No data received from serial port")
            return None
        return data.decode("UTF-8").rstrip()
    except Exception as e:
        logging.error(f"Serial read error: {str(e)}")
        return None


def draw_timer():
    global time_elapsed
    font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 60)
    y = top
    line_t = "{}s".format(round(time_elapsed))
    if int(time_elapsed) > 5:
        draw.text((x, y), line_t, font=font, fill=13)


while True:
    image = Image.new('L', (height, width), 0)
    rotation = -90
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    read_vals = read_serial_safely(usb_serial)
    try:
        valid_input = validate_input(read_vals)
        if valid_input:
            individual_vals = read_vals.split(",")
            is_pump_on = int(individual_vals[6])
            if is_pump_on == 0:
                logging.info(read_vals)
                machine_on = 1
                draw_stats(individual_vals)
                time_elapsed = 0
                start_time = None

            elif is_pump_on == 1:
                if start_time is None:
                    start_time = time.time()
                time_elapsed = time.time() - start_time
                draw_timer()

        else:
            logging.error("Machine values error")
            disp.clear()
            # font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 34)
            # draw.text((x, top), "Error", font=font, fill=13)

        # Display values
        time.sleep(0.1)
        rotated = image.rotate(rotation)
        disp.ShowImage(disp.getbuffer(rotated))

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        disp.module_exit()
        exit()

    except IOError as e:
        logging.info(e)

    except IndexError:
        logging.info("Machine is off")
        machine_on = 0

    except Exception as e:
        logging.error(e)
        exit()
