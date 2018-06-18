# under development.
# tested and worked.

import sys
import traceback
import time
from scapy.all import *
load_contrib('cdp')
load_contrib('lldp')


if len(sys.argv) == 1:
    print('Requires interface name.')
    print('Syntax: python3 scapy_cdp_lldp.py <INTERFACE_NAME>')
    exit()

INTERFACE = sys.argv[1]

class CdpLldpReceiver(threading.Thread):
    def __init__(self):
        super(CdpLldpReceiver, self).__init__()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        eth_cdp = 'ether dst 01:00:0c:cc:cc:cc'
        eth_lldp = 'ether proto 0x88cc'
        filter = '{} or {}'.format(eth_cdp, eth_lldp)

        while not self.stop_event.is_set():
            try:
                sniff(iface=INTERFACE, filter=filter, prn=self.receive, count=0)
            except:
                print('Unable to sniff interface "{}". try again...'.format(INTERFACE))
                time.sleep(5)

    def receive(self, l2frame):
        try:
            dst = l2frame.dst
            if dst == '01:00:0c:cc:cc:cc':
                print('cdp frame received')
                cdp = l2frame[CDPv2_HDR]
                self.receive_cdp(cdp)
            elif '01:80:c2:00:00:0' in dst:
                lldp = l2frame[LLDPDU]
                self.receive_lldp(lldp)
        except:
            #print(traceback.format_exc())
            pass



    def receive_cdp(self, cdp):
        # sample https://gist.github.com/y0ug/8ddb697b5b8a243d0a36
        # impl https://github.com/levigross/Scapy/blob/master/scapy/contrib/cdp.py
        print(cdp[CDPMsgDeviceID].val)
        print(cdp[CDPMsgPortID].iface)
        print(cdp[CDPMsgSoftwareVersion].val)
        print(cdp[CDPMsgPlatform].val)
        print(cdp[CDPMsgNativeVLAN].vlan)

    def receive_lldp(self, lldp):
        # sample
        # impl https://github.com/secdev/scapy/blob/master/scapy/contrib/lldp.py
        try:
            lldp_system_name = lldp[LLDPDUSystemName].system_name.decode()
            text = lldp[LLDPDUSystemDescription].description.decode()
            lldp_system_description = text.replace('\n', '\n    ')
            lldp_port_id = lldp[LLDPDUPortID].id.decode()
            lldp_port_description = lldp[LLDPDUPortDescription].description.decode()
            print('lldp frame received')
            print('system name:        {}'.format(lldp_system_name))
            print('system description: {}'.format(lldp_system_description))
            print('port id:            {}'.format(lldp_port_id))
            print('port description:   {}'.format(lldp_port_description))
            print()
        except:
            pass

    def stop(self):
        self.stop_event.set()
        self.thread.join()

receiver = CdpLldpReceiver()
