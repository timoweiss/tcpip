import socket               # Import socket module
import select
import sys
import time
import struct
from threading import Thread
from threading import Event
from operator import attrgetter
from tcpip_packets import *
import queue



def my_read():      # s i an open UDP socket
    # main loop: repeat until program stops (goon==false)
    got_it=False
    debug=False
    global goon
    while goon:
        try:
            msg, addr = s.recvfrom(2048)    # read from socket
            got_it=True
        except socket.error as e:
            continue
        iph=ipo.unpack(packet)
        linkMap[iph.dst].packet_in(msg,iph)
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

        self.buffer = queue.Queue(maxsize=self.buffersize)
        self.thread = Thread(target=self.sendout).start()
        self.event = Event()

        # you may need some more attributes

    # packet enters
    def packet_in(self,packet,iph):
        print('IN: ', my_time(),'Destination\ID',iph.dst,iph.ids,' size: ',len(packet),'Buffer: ',len(self.buffer))
        try:
            #simulate packetloss
            if simulatePacketLoss and random.randint(0,9) == 5:
                print('PacketLoss simulated throwing away packet for destination %s' %(iph.dst))
            else:
                #try to insert item
                self.buffer.put(packet)
                self.event.set()
        except queue.Full:
            #queue full, throw it away
            print('Queue full throwing away packet for destination %s' %(iph.dst))

    # transmit packet to destination
    def sendout(self):
        try:
            packet = self.buffer.get(True, 3)
            time.sleep(len(packet)/self.bw)
            iph=ipo.unpack(packet)
            print('OUT:', my_time(),'Destination\ID',iph.dst,iph.ids,' size: ',len(packet),'Buffer: ',len(self.buffer))
            s.sendto(packet,self.addr)
        except queue.Empty:
            self.event.clear()
            self.event.wait()

    def sendWithDelay(self,packet):
        time.sleep(self.delay)
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

#create resolving dict
linkMap = dict()
linkMap["141.37.29.1"] = Link("141.37.29.1",('127.0.0.1',50001))
linkMap["141.37.29.2"] = Link("141.37.29.2",('127.0.0.1',50002))

goon=True
my_ip='127.0.0.1'
my_port=6000

ipo=IP('0.0.0.0','0.0.0.0')

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



