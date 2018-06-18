import sys
import time
from datetime import datetime
import socket
import threading
from scapy.all import *

ICMP_ID = 110

if len(sys.argv) <= 2:
    print('Requires destination and MAX_TTL')
    print('Syntax: python3 droppoint_recorder.py <DESTINATION_IP> <MAX_TTL>')
    exit()

DESTINATION_IP = sys.argv[1]
MAX_TTL = int(sys.argv[2])

#### UTIL ####

sequence_dict = {}
lock = threading.Lock()
def sync_add_sendtime(sequence, ttl, destination):
    lock.acquire()
    t = (sequence, ttl, destination, '', 0, time.time(), 0)
    sequence_dict[sequence] = t
    lock.release()

def sync_add_receivetime(sequence, source):
    lock.acquire()
    if sequence in sequence_dict:
        (_, ttl, destination, _, _, send_time, _) = sequence_dict[sequence]
        receive_time = time.time()
        rtt = receive_time - send_time
        sequence_dict[sequence] = (sequence, ttl, destination, source,
                                   rtt, send_time, receive_time)
    lock.release()

def sync_get(sequence):
    lock.acquire()
    t = sequence_dict[sequence]
    lock.release()
    return t

def sync_has(sequence):
    lock.acquire()
    has = sequence in sequence_dict
    lock.release()
    return has


#### RECEIVER ####

class IcmpReceiver(threading.Thread):
    def __init__(self):
        super(IcmpReceiver, self).__init__()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run)

    def run(self):
        # echo-reply or time exceed
        filter = 'icmp[icmptype] == 0 or icmp[icmptype] == 11'
        while not self.stop_event.is_set():
            sniff(filter=filter, prn=self.receive, count=0)

    def receive(self, packet):
        ip = packet[IP]
        icmp = ip[ICMP]
        ip_dst = ip.dst
        ip_src = ip.src
        icmp_id = icmp.id
        icmp_type = icmp.type
        icmp_seq = icmp.seq

        ## Echo reply
        if icmp_type == 0:
            if icmp_id != ICMP_ID:
                return
            sync_add_receivetime(icmp_seq, ip_src)

        ## Time out. Having original packet inside.
        elif icmp_type == 11:
            inner_icmp = IP(icmp.payload)[ICMP]
            icmp_id = inner_icmp.id
            icmp_seq = inner_icmp.seq
            if icmp_id != ICMP_ID:
                return
            sync_add_receivetime(icmp_seq, ip_src)


#### SENDER ####

class IcmpEchoRequestSender(threading.Thread):
    def __init__(self, dst, sequence):
        super(IcmpEchoRequestSender, self).__init__()
        self.dstip = socket.gethostbyname(dst)
        self.sequence = sequence
        self.thread = threading.Thread(target=self.run)

    def run(self):
        for ip_ttl in range(1, MAX_TTL + 1):
            icmp_seq = self.sequence + ip_ttl
            ping = IP(dst=self.dstip, ttl=ip_ttl) / ICMP(id=ICMP_ID, seq=icmp_seq)
            send(ping, verbose=0)
            sync_add_sendtime(icmp_seq, ip_ttl, self.dstip)


#### COLLECTOR ####

class ResultCollector(threading.Thread):
    def __init__(self):
        super(ResultCollector, self).__init__()
        self.thread = threading.Thread(target=self.run)

    def run(self):
        print('timestamp, icmp_sequence, ip_ttl, icmp_destination, icmp_source, rtt')
        sequence = 1
        while(True):
            if not sync_has(sequence):
                # wait and check same sequence again.
                time.sleep(0.1)
                continue

            (seq, ttl, destination, source, rtt, send_time, receive_time) = sync_get(sequence)
            if rtt > 0:
                # has the entry. print.
                timestamp = datetime.fromtimestamp(send_time)
                print('{}, {}, {}, {}, {}, {}'.format(timestamp, seq, ttl, destination, source, rtt))
                sequence += 1

            else:
                diff = time.time() - send_time
                if diff > 5:
                    # judge no response and skip.
                    timestamp = datetime.fromtimestamp(send_time)
                    print('{}, {}, {}, {}, {}, {}'.format(timestamp, seq, ttl, destination, '', -1))
                    sequence += 1

                else:
                    # wait and check same sequence again.
                    time.sleep(0.1)


# Receiver
receiver = IcmpReceiver()
receiver.start()

# Collector
collector = ResultCollector()
collector.start()

# Sender
current_time = 0
last_time = 0
diff_time = 0
sequence = 0
while(True):

    # busy lock. wait 1 sec
    while(True):
        current_time = int(time.time())
        diff_time = current_time - last_time
        if diff_time > 0:
            last_time = current_time
            break
        time.sleep(0.01)

    # send
    thread = IcmpEchoRequestSender(DESTINATION_IP, sequence)
    thread.start()
    sequence += MAX_TTL
