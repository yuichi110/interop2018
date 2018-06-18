import netmiko
import paramiko
import threading
import traceback

DEBUG = True

flag = {
    'cisco_ios':False,
    'cisco_nxos':False,
    'cisco_xr':False,
    'juniper_junos':False,
    'huawei':False,
    'dell_powerconnect':False,
    'a10':True,
    'linux':False,
}


cisco_ios = [
    '172.16.16.3',
    '172.16.16.4',
    '172.16.16.7',
    '172.16.16.10',
    '172.16.16.28'
]

cisco_nxos = [
    '172.16.16.100',
    '172.16.16.101',
    '172.16.16.18',
    '172.16.0.33',
    '172.16.0.31'
]

cisco_xr = [
    '172.16.0.3',
    '172.16.0.8',
    '172.16.0.14',
    '172.16.0.37'
]

juniper_junos = [
    '172.16.0.5',
    '172.16.0.16',
    '172.16.0.20',
    '172.16.0.23',
]

huawei = [
    '172.16.0.11',
    '172.16.17.14',
    '172.16.17.15',
    '172.16.17.16',
    '172.16.17.17',
    '172.16.17.26',
    '172.16.17.32',
    '172.16.17.52',
    '172.16.17.38',
]

dell_powerconnect = [
    '172.16.0.12',
    '172.16.0.24',
    '172.16.1.7',
    '172.16.8.3',
    '172.16.8.4',
    '172.16.9.2',
    '172.16.9.12',
    '172.16.11.51',
    '172.16.11.52',
    '172.16.11.61',
    '172.16.11.71',
    '172.16.12.81',
    '172.16.16.12',
    '172.16.16.13',
    '172.16.16.14',
    '172.16.16.15',
    '172.16.16.16',
    '172.16.16.17'
]

a10 = [
    '172.16.12.11',
    #'172.16.0.27',
    #'172.16.0.28'
]

linux = [
    '172.16.0.34', #cumulus
]



global_lock = threading.Lock()
success_dict = {}
def callback_success(host, result):
    global_lock.acquire()
    success_dict[host] = result
    global_lock.release()

error_dict = {}
def callback_error(host, result):
    global_lock.acquire()
    error_dict[host] = result
    global_lock.release()

class AsyncShow(threading.Thread):
    def __init__(self, device_type, host, show_lists, success_callback, error_callback):
        super(AsyncShow, self).__init__()
        self.device_type = device_type
        self.host = host
        self.show_lists = show_lists
        self.success_callback = success_callback
        self.error_callback = error_callback
        self.thread = threading.Thread(target=self.run)

    def run(self):
        # make ssh session
        try:
            session = netmiko.ConnectHandler(
              device_type=self.device_type,
              host=self.host,
              username='major',
              password='n3zu0tani',
              #verbose=False, optional
            )
            session.enable()
            text = '==== {} ====\n'.format(self.host)
            for show_command in self.show_lists:
                text += '# {}\n'.format(show_command)
                text += session.send_command(show_command)
                text += '\n\n'
            session.disconnect()
            self.success_callback(self.host, text)

        except:
            text = '\nError. Having trouble for accessing host "{}". '.format(self.host)
            text += 'Please check IP reachability and SSH setting.'
            if DEBUG:
                text += '\n\n' + traceback.format_exc() + '\n'
            text += '\n'
            self.error_callback(self.host, text)

# USE PARAMIKO WHEN NETMIKO HAS PROBLEM
class AsyncShow_Paramiko(threading.Thread):
    def __init__(self, host, show_lists, success_callback, error_callback):
        super(AsyncShow_Paramiko, self).__init__()
        self.host = host
        self.show_lists = show_lists
        self.success_callback = success_callback
        self.error_callback = error_callback
        self.thread = threading.Thread(target=self.run)

    def run(self):
        # make ssh session
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
              self.host,
              username = 'major',
              password = 'n3zu0tani',
              look_for_keys = False,
              allow_agent = False,
              timeout = 10,
              auth_timeout = 10)

            text = '==== {} ====\n\n'.format(self.host)
            for show_command in self.show_lists:
                stdin,stdout,stderr = client.exec_command(show_command + '\n')
                for line in stdout:
                    text += line
                text += '\n\n'

            self.success_callback(self.host, text)
            client.close()

        except:
            text = '\nError. Having trouble for accessing host "{}". '.format(self.host)
            text += 'Please check IP reachability and SSH setting.'
            if DEBUG:
                text += '\n\n' + traceback.format_exc() + '\n'
            text += '\n'
            self.error_callback(self.host, text)



thread_list = []

if flag['cisco_ios']:
    for host in cisco_ios:
        thread = AsyncShow('cisco_ios', host, [
        #'show ip int bri | exc una',
        #'show ntp associations',
        'show clock'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

if flag['cisco_nxos']:
    for host in cisco_nxos:
        thread = AsyncShow('cisco_nxos', host, [
        #'show ip int bri | exc una',
        #'show ntp peer-status'
        'show clock'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

if flag['cisco_xr']:
    for host in cisco_xr:
        thread = AsyncShow('cisco_xr', host, [
        #'show ip int bri | exc una',
        #'show ntp associations',
        'show clock'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

if flag['juniper_junos']:
    for host in juniper_junos:
        thread = AsyncShow('juniper_junos', host, [
        #'show interfaces terse | match inet',
        #'show ntp associations'
        'show system uptime'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

if flag['huawei']:
    for host in huawei:
        thread = AsyncShow('huawei', host, [
        #'display ip interface brief | exclude unassigned',
        #'display ntp status | include "clock status"',
        'display clock',
        'display current | inc info'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

if flag['dell_powerconnect']:
    for host in dell_powerconnect:
        # Unable to use Netmiko for dell. Use Paramiko
        thread = AsyncShow_Paramiko(host, [
        #'show interfaces terse | match inet',
        'show ntp associations',
        'show clock',
        'show running | inc logging'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

if flag['a10']:
    for host in linux:
        thread = AsyncShow('a10', host, [
        #'display ip interface brief | exclude unassigned',
        #'ntpq -pn localhost',
        'show ntp status'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

if flag['linux']:
    for host in linux:
        thread = AsyncShow('linux', host, [
        #'display ip interface brief | exclude unassigned',
        #'ntpq -pn localhost',
        'date'
        ], callback_success, callback_error)
        thread.start()
        thread_list.append(thread)

# WAIT ALL THREDS
for t in thread_list:
    print('waiting ssh connection threads....')
    t.join()



# IP ADDRESS BASED SORT RULE
def my_key(item):
    def split_ip(ip):
        """Split a IP address given as string into a 4-tuple of integers."""
        return tuple(int(part) for part in ip.split('.'))
    return split_ip(item[0])

print('\n\nSSH SUCCESS RESULTS\n\n')

# SORT SUCCESS RESULT
items = sorted(success_dict.items(), key=my_key)
for (_, text) in items:
    print(text)


print('\n\nSSH FAILED RESULTS\n\n')

# SORT ERROR RESULT
items = sorted(error_dict.items(), key=my_key)
for (_, text) in items:
    print(text)

'''
Document1
https://pynet.twb-tech.com/blog/automation/netmiko.html

Some Netmiko methods that are generally available to you:
    net_connect.config_mode() -- Enter into config mode
    net_connect.check_config_mode() -- Check if you are in config mode, return a boolean
    net_connect.exit_config_mode() -- Exit config mode
    net_connect.clear_buffer() -- Clear the output buffer on the remote device
    net_connect.enable() -- Enter enable mode
    net_connect.exit_enable_mode() -- Exit enable mode
    net_connect.find_prompt() -- Return the current router prompt
    net_connect.commit(arguments) -- Execute a commit action on Juniper and IOS-XR
    net_connect.disconnect() -- Close the SSH connection
    net_connect.send_command(arguments) -- Send command down the SSH channel, return output back
    net_connect.send_config_set(arguments) -- Send a set of configuration commands to remote device
    net_connect.send_config_from_file(arguments) -- Send a set of configuration commands loaded from a file


Document2
https://github.com/ktbyers/netmiko

Supported Devices

Regularly tested
    Arista vEOS
    Cisco ASA
    Cisco IOS
    Cisco IOS-XE
    Cisco IOS-XR
    Cisco NX-OS
    Cisco SG300
    Dell OS10
    HP Comware7
    HP ProCurve
    Juniper Junos
    Linux

Limited testing
    Alcatel AOS6/AOS8
    Avaya ERS
    Avaya VSP
    Brocade VDX
    Brocade MLX/NetIron
    Calix B6
    Cisco WLC
    Dell-Force10
    Dell PowerConnect
    Huawei
    Mellanox
    NetApp cDOT
    Palo Alto PAN-OS
    Pluribus
    Ruckus ICX/FastIron
    Ubiquiti EdgeSwitch
    Vyatta VyOS

CLASS_MAPPER_BASE = {
    'a10': A10SSH,
    'accedian': AccedianSSH,
    'alcatel_aos': AlcatelAosSSH,
    'alcatel_sros': AlcatelSrosSSH,
    'arista_eos': AristaSSH,
    'aruba_os': ArubaSSH,
    'avaya_ers': AvayaErsSSH,
    'avaya_vsp': AvayaVspSSH,
    'brocade_fastiron': RuckusFastironSSH,
    'brocade_netiron': BrocadeNetironSSH,
    'brocade_nos': BrocadeNosSSH,
    'brocade_vdx': BrocadeNosSSH,
    'brocade_vyos': VyOSSSH,
    'checkpoint_gaia': CheckPointGaiaSSH,
    'calix_b6': CalixB6SSH,
    'ciena_saos': CienaSaosSSH,
    'cisco_asa': CiscoAsaSSH,
    'cisco_ios': CiscoIosSSH,
    'cisco_nxos': CiscoNxosSSH,
    'cisco_s300': CiscoS300SSH,
    'cisco_tp': CiscoTpTcCeSSH,
    'cisco_wlc': CiscoWlcSSH,
    'cisco_xe': CiscoIosSSH,
    'cisco_xr': CiscoXrSSH,
    'coriant': CoriantSSH,
    'dell_force10': DellForce10SSH,
    'dell_powerconnect': DellPowerConnectSSH,
    'eltex': EltexSSH,
    'enterasys': EnterasysSSH,
    'extreme': ExtremeSSH,
    'extreme_wing': ExtremeWingSSH,
    'f5_ltm': F5LtmSSH,
    'fortinet': FortinetSSH,
    'generic_termserver': TerminalServerSSH,
    'hp_comware': HPComwareSSH,
    'hp_procurve': HPProcurveSSH,
    'huawei': HuaweiSSH,
    'huawei_vrpv8': HuaweiVrpv8SSH,
    'juniper': JuniperSSH,
    'juniper_junos': JuniperSSH,
    'linux': LinuxSSH,
    'mellanox': MellanoxSSH,
    'mrv_optiswitch': MrvOptiswitchSSH,
    'netapp_cdot': NetAppcDotSSH,
    'ovs_linux': OvsLinuxSSH,
    'paloalto_panos': PaloAltoPanosSSH,
    'pluribus': PluribusSSH,
    'quanta_mesh': QuantaMeshSSH,
    'ruckus_fastiron': RuckusFastironSSH,
    'ubiquiti_edge': UbiquitiEdgeSSH,
    'ubiquiti_edgeswitch': UbiquitiEdgeSSH,
    'vyatta_vyos': VyOSSSH,
    'vyos': VyOSSSH,
}
'''
