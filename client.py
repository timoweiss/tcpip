
import socket               # Import socket module
import select
import sys
import time
import struct
import math
import helper
from threading import Thread
from threading import Event
from operator import itemgetter
from tcpip_packets import *
import os


# TCP Verbindung
class TCP_Connection(object):

    def __init__(self, srcp, dstp):
        self.dstp = dstp          # Ziel Port
        self.srcp = srcp          # Source Port
        self.mss = 1000           # Maximum Segment Size
        self.rto = 1              # Retransmission timeout (konstant)
        self.state = 'CLOSED'     # Zustand

        self.tx_next = 0          # next segment to transmit
        self.tx_acked = -1        # größtes empfangenes ACK
        self.rx_max = -1          # max segment received in order
        self.tx_max = -1          # maximum byte sent ever
        self.segments_in_flight = []  # segments in flight
        # list of (info, segment) tupels
        # save seq and ackn
        self.seq=0
        self.ackn=0

        self.cwnd = 1             # congestion window
        self.rwnd = 8             # receive window
        self.dupACKs = 0          # duplicate ACKs
        self.ssthresh = 8         # slow start threshold
        self.n_rtx = 0            # number of current retransmissions
        self.max_rtx = 5          # maximum number of retransmissions
        self.buffered_packets = sorted([], key=itemgetter(0))
        # buffer for packets received out of order

        # TCP object for generating and analyzinig TCP packets
        self.segment = TCP(srcp, dstp)
        # see tcpip_packet.py

    # print state of connection
    def pr(self):
        print(self.state + ', tx_next:', self.tx_next,
              ', tx_max:', self.tx_max, end='')
        print(' tx_acked:', self.tx_acked, ', cwnd:', self.cwnd,
              ' flight:', len(self.segments_in_flight))

    # send request, get ACK, retrieve data
    def request_data(self, n):
        self.num_segments = n
        if not self.connect():
            print('Connection establihsment failed')
            return False
        print('Connection established, sending request')
        if not self.send_request():
            return False
        if not self.wait_ack():
            return False
        print('Request acked, retreiving data ...')
        if not self.receive_data():
            return False
        print('Data received, closing connection')
        return self.close()

    # establish TCP connection
    def connect(self):
        self.seq=0
        self.ackn=0
        # build syn
        packet = tcpo.gen_packet(seqn=0, syn=1)
        # send syn
        info = self.segment.get_info(packet)
        helper.print_info(info, 'syn OUT:')
        self.send_packet(packet)

        # wait for response
        packet = receive_segment(3)
        info = self.segment.get_info(packet)
        helper.print_info(info, 'syn ack IN:')
        # syn ack
        # seqn = 0, ackn = my_seqn+1
        if(info == (0, 1, True, True, 0, False)):
            packet = tcpo.gen_packet(seqn=1,ackn=1, ack=1)
            info = self.segment.get_info(packet)
            helper.print_info(info, 'ack OUT:')
            self.send_packet(packet)
            return True
        return False

    # send the request containing the number of segments
    def send_request(self):
        # increment sequence number
        self.seq += 1

        payload = struct.pack('i', self.num_segments)
        #payload = b''
        #seqn=self.tx_next,payload=payload,ackn=self.rx_max+1
        packet = tcpo.gen_packet(seqn=self.seq, ackn=self.ackn, payload=payload)
        info = self.segment.get_info(packet)
        helper.print_info(info, 'OUT:')
        self.send_packet(packet)

        return True

    def wait_ack(self):
        packet = receive_segment(3)
        info = self.segment.get_info(packet)
        helper.print_info(info, 'IN:')

        self.seq = info[0] + 1
        self.ackn = info[1]
        # ack
        if(info[3]):
            packet=self.segment.gen_packet(self.seq,ackn=self.ackn,ack=1)
            self.send_packet(packet)
            self.segments_in_flight.pop(0)
            return True
        return


    # function to receive data
    def receive_data(self):
        while goon:
            packet = receive_segment(5)
            info = self.segment.get_info(packet)
            helper.print_info(info, 'IN:')
            if packet != []:
                seqn, ackn, syn, ack, payload, fin = self.segment.get_info(
                    packet)
                data = self.segment.unpack(packet)
                #print(data.payload)
                # TODO errorhandling
            return True
        return False

    # function to execute closing procedure
    def close(self):
        packet = tcpo.gen_packet(self.seq,fin=1,ackn=self.ackn)
        info = self.segment.get_info(packet)
        helper.print_info(info, 'OUT:')
        self.send_packet(packet)
        packet = receive_segment(5)
        info = self.segment.get_info(packet)
        helper.print_info(info, 'IN:')
        if(info[5]):
            packet = tcpo.gen_packet(self.seq, ack=1,ackn=self.ackn)
            info = self.segment.get_info(packet)
            helper.print_info(info, 'OUT:')
            self.send_packet(packet)

        return True

    # send an ack: recommended to send all ACK using this function
    def send_ack(self):
        pass    # TODO: Schritt 1-3, Aufgabe 4

        # this should be used to generate packets
        # seqn, ackn,syn, fin,ack, payload need to be modified according to the
        # packet to be sent
        packet = self.segment.gen_packet(seqn, ackn, syn, fin, ack, payload)
        # this function should be used to put them on the UDP socket
        info = self.segment.get_info(packet)
        helper.print_info(info, 'OUT:')
        self.send_packet(packet)

    # implement a function to trigger retransmits
    # function should return false in number of retransmissions is exceeded
    def rtx_packet(self):
        pass    # TODO: Schritt 1-3

    # this function should be used to send packets with payload
    # Funktion kann unverändert verwendet werden.
    # Je nach Implementierung kann eine Adaption vorgenommen werden
    def send_packet(self, packet):
        self.segments_in_flight.append((self.segment.get_info(packet), packet))
        send_segment(packet, self.segment.get_info(packet))


# function to receive packet from UDP socket, print the information and extract TCP packet
# Funktion kann unverändert verwendet werden
def receive_segment(rto):
    # function times out after rto
    s.settimeout(rto)
    # receive packet
    try:
        packet, addr = s.recvfrom(2048)    # read from socket
    except socket.timeout:
        # in case of error or timeout return []
        return []
    except socket.error as e:
        print(e)
        return []
    # extract header fields from binary packet
    iph = ipo.unpack(packet)
    #helper.print_in_msg(packet, ipo.id, 'IN:')
    if iph.dst != my_v_ip:
        print('Error: IP packet not addressed to me', iph.dst)
        return
    # extract information from TCP Packet
    # packet[20:]:packet without 20 Bytes IP header
    # TODO: self ist nicht definiert
    #info = self.segment.get_info(packet[20:])
    #print_packet('IN: ', ipo.id, info)
    # return TCP packet
    return packet[20:]


# this function sends packets on the UDP socket
# Funktion kann unverändert verwendet werden
def send_segment(packet, info):
    time.sleep(2)
    #print_packet('OUT:', ipo.id, info)
    #helper.print_in_msg(packet, ipo.id, 'OUT2:')
    # create IP header
    iph = ipo.pack()
    # add IP header
    packet = iph + packet
    # send packet
    s.sendto(packet, (dst_ip, dst_port))


# function to print information for a packet
def print_packet(s, pid, info):
    print(s + ' ' + my_time() + ' ID:' + str(pid), end='')
    print(' SEQ:' + str(info[0]) + '-' + str(info[0] + info[4]), end='')
    print(' Payload: ' + str(info[4]), end='')
    print(' ACK:' + str(info[1]) + ' ', end='')
    if info[2]:
        print('S', end='')
    if info[3]:
        print('A', end='')
    if info[5]:
        print('F', end='')
    print()

# get time in acceptable format


def my_time():
    return '{:+3.3f}'.format(time.time() % 1e3)

# the client, started as a thread


def my_file_client():
    conn = TCP_Connection(my_v_port, dst_v_port)
    if conn.request_data(num_segments):
        print('Retrieved file and close connection')
    else:
        print('Failed')
    goon = False

def gen_payload():
    return os.urandom(1000)
# global data
goon = True               # Threads stop if goon==0

# real and virtual addresses and port
# TODO: Adressen bei Bedarf richtig konfigurieren
my_port = 5000
dst_port = 6000
my_ip = '127.0.0.1'
dst_ip = '127.0.0.1'
my_v_ip = '141.37.168.2'
dst_v_ip = '141.37.168.1'
my_v_port = 1000
dst_v_port = 100

# number of segments requested
# TODO: für Schritt 4 anpassen
num_segments = 1

# open a udp socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((my_ip, my_port))

# generic IP object for generating and extracting IP headers
ipo = IP(my_v_ip, dst_v_ip)

# generic TCP object for generating and extracting IP headers
tcpo = TCP(0, 0)
tcpo.pack()

# thread for the client
t_file = Thread(target=my_file_client)
t_file.start()

# possibility to quit
while goon:
    time.sleep(1)
    action = input('Enter Action (<Q>)\n')
    if action == 'Q':
        print('Quitting')
        goon = False
