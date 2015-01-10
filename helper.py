import struct

class layer():
    pass


def get_packet_info(packet):
    cflags = {  # Control flags
        32: "U",
        16: "A",
        8: "P",
        4: "R",
        2: "S",
        1: "F"}
    _tcp = layer()
    _tcp.thl = ((packet[12]) >> 4) * 4
    _tcp.options = packet[20:_tcp.thl]
    _tcp.payload = packet[_tcp.thl:]
    tcph = struct.unpack("!HHLLBBHHH", packet[:20])
    _tcp.srcp = tcph[0]  # source port
    _tcp.dstp = tcph[1]  # destination port
    _tcp.seq = tcph[2]  # sequence number
    _tcp.ack = tcph[3]  # acknowledgment number
    _tcp.flags = ""
    for f in cflags:
        if tcph[5] & f:
            _tcp.flags += cflags[f]
    _tcp.window = tcph[6]  # window
    _tcp.checksum = hex(tcph[7])  # checksum
    _tcp.urg = tcph[8]  # urgent pointer
    _tcp.list = [
        _tcp.srcp,
        _tcp.dstp,
        _tcp.seq,
        _tcp.ack,
        _tcp.thl,
        _tcp.flags,
        _tcp.window,
        _tcp.checksum,
        _tcp.urg,
        _tcp.options]
    _tcp.syn = _tcp.flags.find("S") != -1
    _tcp.isACK = _tcp.flags.find("A") != -1
    _tcp.fin = _tcp.flags.find("F") != -1
    return _tcp

def print_in_msg(packet, ipo_id):
    pi = get_packet_info(packet)
    print('IN:', 'seqn:', pi.seq, 'ackn:', pi.ack, 'syn:', pi.syn, 'fin:', pi.fin, 'ack:', pi.isACK)
