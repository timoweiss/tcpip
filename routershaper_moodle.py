import socket               # Import socket module
import select
import sys
import time
import struct
from threading import Thread
from threading import Event
from operator import attrgetter
from tcpip_packets import *


def my_read():      # s i an open UDP socket
    # main loop: repeat until program stops (goon==false)
    got_it=False
    debug=False
    while goon:
        try:                       
            msg, addr = s.recvfrom(2048)    # read from socket
            got_it=True
        except socket.error as e:
            continue
        iph=ipo.unpack(packet)

        # deal with packet
        # check whether destination is known
        # insert into buffer


def my_time():
    return '{:+3.3f}'.format(time.time()%1e3)

# object to handle link to a destination
class Link(object):
    def __init__(self, v_dst, addr):
        self.v_dst=v_dst
        self.addr=addr
        self.buffersize=5
        self.delay=0.1
        self.bw=1040/0.1

        # you may need some more attributes

    # packet enters
    def packet_in(self,packet,iph):
        print('IN: ', my_time(),'Destination\ID',iph.dst,iph.ids,' size: ',len(packet),'Buffer: ',len(self.buffer))


    # transmit packet to destination
    def sendout(self,delay,packet,iph):
        print('OUT:', my_time(),'Destination\ID',iph.dst,iph.ids,' size: ',len(packet),'Buffer: ',len(self.buffer))
        s.sendto(packet,self.addr)
        
def my_quit():
    global goon
    print('Quitting!!!')
    goon=0
    

def my_input():
    global action
    time.sleep(1)
    action=input('Enter Action (<Q>)\n')
    actions[action]()
                    

goon=True
my_ip='127.0.0.1'
my_port=6000

ipo=IP(0,'0.0.0.0','0.0.0.0')

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((my_ip, my_port))
s.settimeout(5)
t_read=Thread(target=my_read)
t_read.start()

actions = {'Q' : my_quit }
while goon:
    t_in=Thread(target=my_input)
    t_in.start()
    t_in.join()
    
sys.exit()



