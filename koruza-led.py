from bibliopixel.drivers.LPD8806 import *
from bibliopixel import LEDStrip
#import the module you'd like to use
from BiblioPixelAnimations.strip import LarsonScanners

#fadecandy stuff
import opc, time
import colorsys
import threading
import time

import json
import requests
import math


def get_sfp(host):
    """
    Fetches SFP diagnostic data from a KORUZAv2 unit via uBus.
    
    :param host: KORUZAv2 unit hostname/ip to connect to
    """
    
    url = 'http://{}/ubus'.format(host)
    payload = {
        'jsonrpc': '2.0',
        'method': 'call',
        'id': 1,
        'params': ['00000000000000000000000000000000', 'sfp', 'get_diagnostics', {}]
    }
    return requests.post(url, data=json.dumps(payload)).json()['result'][1].values()[0]['value']

diagnostics1 = get_sfp('10.254.39.73')
diagnostics2 = get_sfp('10.254.39.113')
print "RX Power: {} mW".format(float(diagnostics1['rx_power']))
print "RX Power: {} mW".format(float(diagnostics2['rx_power']))

num_leds = 24
tail_length = 24

def average_power_db():
    diagnostics1 = get_sfp('10.254.39.73')
    avg=float(diagnostics1['rx_power'])
    if not avg:
        return -10

    return 10 * math.log10(avg * 10000) - 10



def spinning():
    for count in range(num_leds):
        pixels = [ (0,0,0) ] * num_leds
        value=average_power_db()*15
        for tl in range(tail_length):
			#pixels[tl-count] =(255/tail_length*(tail_length-tl),0,0) # RGB color linera Fade
            div=255/tail_length*(tail_length-tl)
            pixels[tl-count] = wheel_color(value,div) # RGB color
        pixels = pixels + [ (0,0,0) ] * 36 + pixels
        client.put_pixels(pixels)
        time.sleep(0.05)

def wheel_color(position,div):
    """Get color from wheel value (0 - 384)."""

    if position < 0:
        position = 0
    if position > 384:
        position = 384

    if position < 128:
        r = 127 - position % 128
        g = position % 128
        b = 0
    elif position < 256:
        g = 127 - position % 128
        b = position % 128
        r = 0
    else:
        b = 127 - position % 128
        r = position % 128
        g = 0

    return r*div/100, b*div/100, g*div/100

def one_circle():
    num_leds = 24
    tail_length = 24
    for count in range(num_leds):
        pixels = [ (0,0,0) ] * num_leds
        for tl in range(tail_length):
			#pixels[tl-count] =(255/tail_length*(tail_length-tl),0,0) # RGB color linera Fade
            div=255/tail_length*(tail_length-tl)
            pixels[tl-count] = wheel_color(1,div) # RGB color
        client.put_pixels(pixels)
        time.sleep(0.05)
    return

def cirlce_blank():
    num_leds = 24
    pixels = [ (0,0,0) ] * num_leds
    client.put_pixels(pixels)
    time.sleep(0.05)
    return

def circle_fade():
    num_leds = 24
    black = [ (0,0,0) ] * num_leds
    client.put_pixels(black)
    time.sleep(1)
    color = [ (255,0,0) ] * num_leds
    client.put_pixels(color)
    time.sleep(1)
    client.put_pixels(black)

    return


client = opc.Client('localhost:7890')

#digital strip stuff

#init driver with the type and count of LEDs you're using
numLeds = 120
driver = DriverLPD8806(numLeds, c_order = ChannelOrder.BRG,use_py_spi = True, dev="/dev/spidev0.0", SPISpeed = 16)

#init controller
led = LEDStrip(driver)

#init animation; replace with whichever animation you'd like to use
anim = LarsonScanners.LarsonScanner(led,(255,0,0))

# Define a function for the thread
class thread_lights (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print "Starting " + self.name
        # Get lock to synchronize threads
        #threadLock.acquire()
        if self.counter==1:
            while 1:
                # Do stuff
               #cirlce_blank()
               #circle_fade()
               #time.sleep(2.2)
               #circle_fade()
               spinning()
        elif self.counter==2:
            while 1:
               time.sleep(2)
               #run the animation
               #print "%s: %s" % ( "Start strip move", time.time() )
               #delay_time = time.time()
               if average_power_db() > 0 :
                   anim = LarsonScanners.LarsonScanner(led,(255,0,0))
                   anim.run(fps=100, untilComplete=True, max_cycles=1)
               #print "%s: %s %s" % ( "Stop strip move", time.time(), time.time()-delay_time )
               led.all_off()
               led.update()

        # Free lock to release next thread
        #threadLock.release()

threadLock = threading.Lock()
threads = []

# Create new threads
thread1 = thread_lights(1, "Thread-1", 1)
thread2 = thread_lights(2, "Thread-2", 2)

try:

    #while 1:

    # Create new threads
    thread1 = thread_lights(1, "Thread-1", 1)
    thread2 = thread_lights(2, "Thread-2", 2)

    # Start new Threads
    thread1.start()
    thread2.start()

    # Add threads to thread list
    threads.append(thread1)
    threads.append(thread2)

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print "Exiting Main Thread"

except KeyboardInterrupt:
    #Ctrl+C will exit the animation and turn the LEDs offs
    led.all_off()
    led.update()

