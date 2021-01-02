import xled
from PIL import Image
import io
import struct
from xled.compat import xrange
from random import randint
import socket
import time
import base64
import math

import logging

logging.basicConfig(level=logging.DEBUG)


def doit():
    discovered_device = xled.discover.discover()
    ip = discovered_device.ip_address
    hw = discovered_device.hw_address
 #   ip = "192.168.7.1"
 #   hw = "12:33"

    control = xled.ControlInterface(ip, hw)
    control.set_mode('movie')
    info = control.get_device_info()
    print(info.data)
    info2 = control.firmware_version()
    print(info2.data)

    hi = xled.HighControlInterface(ip, hw)
#    hi.turn_on()
#    print(hi.is_on())

#    set_static_color2(hi, 0,0,0)

#    print("hopp")
#    hi.turn_off()


def do_gif():
    im = Image.open("./piskel.gif")
    print(im.is_animated)
    print(im.n_frames)

    # Display individual frames from the loaded animated GIF file
    for frame in range(0,im.n_frames):
        im.seek(frame)
        rgb_im = im.convert('RGB')
        print("Frame: ", im.tell())

        print("width")
        print(im.width)

        for x in range(im.width):
            for y in range(im.height):
                r, g, b = rgb_im.getpixel((x, y))

                print('[', r, ',', g, ',',b, ']', end='')



def do_gif_movie(xled_control, gif_file, delay=None):
    im = Image.open(gif_file)
    assert(im.is_animated)
    assert(im.n_frames > 1)

    if not delay:
        # Assume delays are uniform for all frames, and use the value
        # of the first framme
        delay = im.info['duration']

    response = xled_control.get_device_info()
    number_of_led = response["number_of_led"]
    assert(number_of_led == im.width * im.height)

    with io.BytesIO() as output:
        for frame in range(0, im.n_frames):
            im.seek(frame)
            rgb_im = im.convert('RGB')
            for x in range(im.width):
                for y in range(im.height):
                    r, g, b = rgb_im.getpixel((x, y))
                    # white, red, green, blue
             #       print('[', r, ',', g, ',',b, ']', end='')
                    if g == 36 and b == 36:
                        g = 0
                        b = 0
                    bytes_str = struct.pack(">BBBB", 0, r, g, b)
                    output.write(bytes_str)


        xled_control.set_mode('movie')
        xled_control.led_reset()
        output.seek(0)
        xled_control.set_led_movie_full(output)
        xled_control.set_led_movie_config(delay, im.n_frames, number_of_led)


def doit_with_gif():
#    discovered_device = xled.discover.discover()
#    ip = discovered_device.ip_address
#    hw = discovered_device.hw_address
  #  ip = "192.168.7.1"
  #  hw = "12:33"
    ip = "192.168.1.106"
    hw = "98:f4:ab:38:7d:f5"


    control = xled.ControlInterface(ip, hw)
    # In general, for x FPS the delay should be 1000/x.
    do_gif_movie(control, "./Y2021_mirror.gif", 1500)


def write_static_movie_frame(file_obj, size, white, red, green, blue):
    """
    Writes movie of single color

    :param int size: numbers of triples (RGB) to write to.
    :param red: integer between 0-255 representing red color
    :param green: integer between 0-255 representing green color
    :param blue: integer between 0-255 representing blue color
    """
    assert red in range(0, 256)
    assert green in range(0, 256)
    assert blue in range(0, 256)
    bytes_str = struct.pack(">BBBB", white, red, green, blue)
    for position in xrange(size):
        file_obj.write(bytes_str)

def create_realtime_udp_header(control, output, number_of_leds, bytes_per_led):
    """
    Creates a single packet UDP header for realtime frame

    :param output: file-like object to write UDP header to.
    :param int number_of_leds: the number of LEDs in the frame
    :param int bytes_per_led: the number of bytes per LED  (3 or 4)
    """
    assert(number_of_leds*bytes_per_led <= 900)
    assert(number_of_leds <= 255)
    output.write(b'\x01')
    token_bytes = base64.b64decode(control.session.access_token)
    output.write(token_bytes)
    output.write(number_of_leds.to_bytes(1, byteorder='big'))

def create_realtime_udp_header_multi(self, control, output, this_packet):
    """
    Creates a multipacket UDP header for realtime frame

    :param output: file-like object to write UDP header to.
    :param int number_of_leds: the number of LEDs in the frame
    :param int bytes_per_led: the number of bytes per LED  (3 or 4)
    """
    output.write(b'\x03')
    token_bytes = base64.b64decode(control.session.access_token)
    output.write(token_bytes)
    output.write()
    output.write(this_packet.to_bytes(1, byteorder='big'))

UDP_PORT = 7777


def send_realtime():
    discovered_device = xled.discover.discover()
    ip = discovered_device.ip_address
    hw = discovered_device.hw_address
  #  ip = "192.168.7.1"
  #  hw = "12:33"

    control = xled.ControlInterface(ip, hw)
    control.set_mode('rt')

    hi = xled.HighControlInterface(ip, hw)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

    for i in range(0, 255):
        with io.BytesIO() as output:
            hi.create_realtime_udp_header(control, output, 210, 4)
            write_static_movie_frame(output, 210, 0, 0, i, 0)
            output.seek(0)

            print("writing frame {}".format(i))
            ba = output.read()
            sock.sendto(ba, (ip, UDP_PORT))
            time.sleep(0.1)

    return
    for i in range(0, 255):
        with io.BytesIO() as output:
            hi.create_realtime_udp_header_multi(control, output, 0)
            write_static_movie_frame(output, 50, 0, i, 0, 0)
            output.seek(0)

            print("writing frame {}".format(i))
            ba = output.read()
            sock.sendto(ba, (ip, UDP_PORT))

        with io.BytesIO() as output:
            hi.create_realtime_udp_header_multi(control, output, 1)
            write_static_movie_frame(output, 160, 0, 0, i, 0)
            output.seek(0)

            print("writing frame {}".format(i))
            ba = output.read()
            sock.sendto(ba, (ip, UDP_PORT))

def send_realtim2():
#    discovered_device = xled.discover.discover()
#    ip = discovered_device.ip_address
#    hw = discovered_device.hw_address
    ip = "192.168.1.106"
    hw = "98:f4:ab:38:7d:f4"

    control = xled.ControlInterface(ip, hw)
    control.set_mode('rt')

    for i in range(0, 255):
        with io.BytesIO() as output:
            write_static_movie_frame(output, 210, 0, 0, i, 0)
            output.seek(0)

            ba = output.read()
            control.send_realtime_frame(210, 4, ba)
            time.sleep(0.1)

    return

def test_new():
    discovered_device = xled.discover.discover()
  #  ip = discovered_device.ip_address
  #  hw = discovered_device.hw_address
    ip = "192.168.1.106"
    hw = "98:f4:ab:38:7d:f4"

    control = xled.ControlInterface(ip)
    control.set_mode('demo')

    time.sleep(1)

    hi = xled.HighControlInterface(ip)
    hi.turn_off()

#doit()
#do_gif()
doit_with_gif()
#send_realtim2()
#test_new()