'''
Interop 2018
Drop test script for Mac.

Please use this tool with python3 as root user.
Since ping6 with size option requires root.
1. sudo -s
2. Be root
3. python3 dropcheck.py
'''

# please update your nic info. en0 and en8 are my PC own.
wifi_list = ['en0']
nic_list = ['en8',
  # please remove comment out of vlan when you use trunk port
  # 'vlan0', 'vlan1', 'vlan2', 'vlan3', 'vlan4', 'vlan5',
]

command_list = [
  # syntax
  # (priority:low is high, command)
  # 0-100 are used in basic tests. please use 101 and later.

  # v4 checks
  # ping to gateway checks are generated in function "check_default_route()"
  #(101, 'ping -c 3 -D -s 500 8.8.8.8 2>&1 | cat'), # -c : count, -D : don't flagment, -s size
  (102, 'ping -c 3 -D -s 1472 8.8.8.8 2>&1 | cat'),
  #(111, 'traceroute -n -m 10 -q1 -w1 8.8.8.8 2>&1 | cat'), # -m means max_ttl. If 10 is not enough please add.
  (111, './mtr -n -c 100 -i 0.1 -wb --report 8.8.8.8 2>&1 | cat'),
  (121, 'dig +short www.wide.ad.jp  2>&1 | cat'), # +short means short option
  #(131, 'wget --spider http://www.nicovideo.jp 2>&1 | grep response'), # --spider means not download but check file existance
  # you should test web access via browser too. It can detect other difficult problems...

  # v6 checks
  # ping6 to gateway checks are generated in function "check_default_route()"
  #(103, 'ping6 -c 3 -D -s 500 2001:4860:4860::8888 2>&1 | cat'),
  (104, 'ping6 -c 3 -D -s 1232 2001:4860:4860::8888 2>&1 | cat'),
  #(105, 'ping6 -c 3 -D -s 1432 2001:4860:4860::8888 2>&1 | cat'),
  #(112, 'traceroute6 -n -m 10 -q1 -w1 2001:4860:4860::8888 2>&1 | cat'),
  (112, './mtr -n -c 100 -i 0.1 -wb --report -6 2001:4860:4860::8888 2>&1 | cat'),
  (122, 'dig +short www.wide.ad.jp AAAA 2>&1 | cat'),
  #(132, 'wget --spider http://ipv6.google.com 2>&1 | grep response')
]

import subprocess
import threading
import time

# issuing commands too fast make ping6 small trouble. might be command bug.
SLEEP_TIME = 0.3
PINGV4_GATEWAY_SIZE_LIST = [1472]
PINGV6_GATEWAY_SIZE_LIST = [1232]


## Utility

command_threads = []
result_dict = {}
lock = threading.Lock()
def sync_add_result(counter, result):
    lock.acquire()
    result_dict[counter] = result
    lock.release()

def get_pipe_command_result(command):
    proc = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout_data, stderr_data) = proc.communicate()
    return (stdout_data.decode(), stderr_data.decode())

def convert_ip_to_host(text):
    convert_dict = {
        "45.0.3.1 ":"300--xhg-0-0-0-3.asr9904.fp1 (45.0.3.1) ",
        "45.0.3.2 ":"300--hg-0-0-5.qfx10002.fp1 (45.0.3.2) ",
        "45.0.3.5 ":"301.vrf-srx4600.asr9904.fp1 (45.0.3.5) ",
        "45.0.3.6 ":"301.srx4600-top.fp1 (45.0.3.6) ",
        "45.0.3.9 ":"302.vrf-srx4600.asr9904.fp1 (45.0.3.9) ",
        "45.0.3.10 ":"302.srx4600-bot.fp1 (45.0.3.10) ",
        "45.0.3.13 ":"303.vrf-asr1001hx.asr9904.fp1 (45.0.3.13) ",
        "45.0.3.14 ":"303.asr1002hx-top.fp1 (45.0.3.14) ",
        "45.0.3.17 ":"304.vrf-asr1001hx.asr9904.fp1 (45.0.3.17) ",
        "45.0.3.18 ":"304.asr1002hx-bot.fp1 (45.0.3.18) ",
        "45.0.3.21 ":"305.asr1002hx-backup-top.fp1 (45.0.3.21) ",
        "45.0.3.22 ":"305.asr1002hx-backup-bot.fp1 (45.0.3.22) ",
        "45.0.3.25 ":"306.lastline-top.fp1 (45.0.3.25) ",
        "45.0.3.26 ":"306.lastline-bot.fp1 (45.0.3.26) ",
        "45.0.3.29 ":"307.lastline (45.0.3.29) ",
        "45.0.3.30 ":"307.lastline (45.0.3.30) ",
        "45.0.3.33 ":"308.lastline-backup-top.fp1 (45.0.3.33) ",
        "45.0.3.34 ":"308.lastline-backup-bot.fp1 (45.0.3.34) ",
        "45.0.3.37 ":"309.tippingpoint-top.fp1 (45.0.3.37) ",
        "45.0.3.38 ":"309.tippingpoint-bot.fp1 (45.0.3.38) ",
        "45.0.3.41 ":"310.tippingpoint (45.0.3.41) ",
        "45.0.3.42 ":"310.tippingpoint (45.0.3.42) ",
        "45.0.3.45 ":"311.tippingpoint-backup-top.fp1 (45.0.3.45) ",
        "45.0.3.46 ":"311.tippingpoint-backup-bot.fp1 (45.0.3.46) ",
        "45.0.3.49 ":"312.threatarmor-top.fp1 (45.0.3.49) ",
        "45.0.3.50 ":"312.threatarmor-bot.fp1 (45.0.3.50) ",
        "45.0.3.53 ":"313.threatarmor (45.0.3.53) ",
        "45.0.3.54 ":"313.threatarmor (45.0.3.54) ",
        "45.0.3.57 ":"313.threatarmor-backup-top.fp1 (45.0.3.57) ",
        "45.0.3.58 ":"313.threatarmor-backup-bot.fp1 (45.0.3.58) ",
        "45.0.3.61 ":"315.fg6300f-top.fp1 (45.0.3.61) ",
        "45.0.3.62 ":"315.fg6300f-bot.fp1 (45.0.3.62) ",
        "45.0.3.65 ":"316.fg6300f (45.0.3.65) ",
        "45.0.3.66 ":"316.fg6300f (45.0.3.66) ",
        "45.0.3.69 ":"317.fg6300f-backup-top.fp1 (45.0.3.69) ",
        "45.0.3.70 ":"317.fg6300f-backup-bot.fp1 (45.0.3.70) ",
        "45.0.3.85 ":"321.vrf-th7740cfw.mx204-top.fp2 (45.0.3.85) ",
        "45.0.3.86 ":"321.th7740cfw-1-top.fp2 (45.0.3.86) ",
        "45.0.3.89 ":"322.vrf-th7740cfw.mmx204-bot.fp2 (45.0.3.89) ",
        "45.0.3.90 ":"322.th7740cfw-1-bot.fp2 (45.0.3.90) ",
        "45.0.3.93 ":"323.vrf-th7740cfw-2.mx204-top.fp2 (45.0.3.93) ",
        "45.0.3.94 ":"323.th7740cfw-2-top.fp2 (45.0.3.94) ",
        "10.0.3.97 ":"324.vrf-th7740cfw-2.mx204-bot.fp2 (10.0.3.97) ",
        "10.0.3.98 ":"324.th7740cfw-2-bot.fp2 (10.0.3.98) ",
        "45.0.3.101 ":"325.firepower9300-top.fp2 (45.0.3.101) ",
        "45.0.3.102 ":"325.firepower9300-bot.fp2 (45.0.3.102) ",
        "45.0.3.109 ":"327.firepower9300-backup-top.fp2 (45.0.3.109) ",
        "45.0.3.110 ":"327.firepower9300-backup-bot.fp2 (45.0.3.110) ",
        "45.0.3.113 ":"328.pa5280-top.fp2 (45.0.3.113) ",
        "45.0.3.114 ":"328.pa5280-bot.fp2 (45.0.3.114) ",
        "45.0.3.129 ":"332.pa5280-backup-top.fp2 (45.0.3.129) ",
        "45.0.3.130 ":"332.pa5280-backup-bot.fp2 (45.0.3.130) ",
        "45.0.3.121 ":"330.pa5280-captive-top.fp2 (45.0.3.121) ",
        "45.0.3.122 ":"330.pa5280-captive-bot.fp2 (45.0.3.122) ",
        "45.0.3.133 ":"333.pa5280-captive-backup-top.fp2 (45.0.3.133) ",
        "45.0.3.134 ":"333.pa5280-captive-backup-bot.fp2 (45.0.3.134) ",
        "45.0.3.137 ":"334.s4048on-top.fp2 (45.0.3.137) ",
        "45.0.3.138 ":"334.s4048on-bot.fp2 (45.0.3.138) ",
        "45.0.3.145 ":"336.s4048on-backup-top.fp2 (45.0.3.145) ",
        "45.0.3.146 ":"336.s4048on-backup-bot.fp2 (45.0.3.146) ",

        # test
        #"45.0.1.81 ":"test1 (45.0.1.81)",
        #"2001:3e8:0:120::7 ":"test2 (2001:3e8:0:120::7)",

        "2001:3e8:0:358::15 ":"358.from-fp1-to-fp2.asr9904.fp1 (2001:3e8:0:358::15) ",
        "2001:3e8:0:358::16 ":"358.from-fp1-to-fp2.mx204.fp2 (2001:3e8:0:358::16) ",
        "2001:3e8:0:359::15 ":"359.from-fp1-to-fp3.asr9904.fp1 (2001:3e8:0:359::15) ",
        "2001:3e8:0:359::17 ":"359.from-fp1-to-fp3.ne40e-m2k.fp3 (2001:3e8:0:359::17) ",
        "2001:3e8:0:360::15 ":"360.from-fp2-to-fp1.asr9904.fp1 (2001:3e8:0:360::15) ",
        "2001:3e8:0:360::16 ":"360.from-fp2-to-fp1.mx204.fp2 (2001:3e8:0:360::16) ",
        "2001:3e8:0:361::16 ":"361.from-fp2-to-fp3.mx204.fp2 (2001:3e8:0:361::16) ",
        "2001:3e8:0:361::17 ":"361.from-fp2-to-fp3.ne40e-m2k.fp3 (2001:3e8:0:361::17) ",
        "2001:3e8:0:362::15 ":"362.from-fp3-to-fp1.asr9904.fp1 (2001:3e8:0:362::15) ",
        "2001:3e8:0:362::17 ":"362.from-fp3-to-fp1.ne40e-m2k.fp3 (2001:3e8:0:362::17) ",
        "2001:3e8:0:363::16 ":"363.from-fp3-to-fp2.mx204.fp2 (2001:3e8:0:363::16) ",
        "2001:3e8:0:363::17 ":"363.from-fp3-to-fp2.ne40e-m2k.fp3 (2001:3e8:0:363::17) ",
        "2001:3e8:0:301::1 ":"301--srx4600.fp1 (2001:3e8:0:301::1) ",
        "2001:3e8:0:302::1 ":"302--srx4600.fp1 (2001:3e8:0:302::1) ",
        "2001:3e8:0:303::1 ":"303--asr1002hx.fp1 (2001:3e8:0:303::1) ",
        "2001:3e8:0:304::1 ":"304--asr1002hx.fp1 (2001:3e8:0:304::1) ",
        "2001:3e8:0:305::1 ":"305--asr1002hx-backup.fp1 (2001:3e8:0:305::1) ",
        "2001:3e8:0:306::1 ":"306--lastline.fp1 (2001:3e8:0:306::1) ",
        "2001:3e8:0:307::1 ":"307--.fp1 (2001:3e8:0:307::1) ",
        "2001:3e8:0:308::1 ":"308--lastline-backup.fp1 (2001:3e8:0:308::1) ",
        "2001:3e8:0:309::1 ":"309--tippingpoint.fp1 (2001:3e8:0:309::1) ",
        "2001:3e8:0:310::1 ":"310--.fp1 (2001:3e8:0:310::1) ",
        "2001:3e8:0:311::1 ":"311--tippingpoint-backup.fp1 (2001:3e8:0:311::1) ",
        "2001:3e8:0:312::1 ":"312--threatarmor.fp1 (2001:3e8:0:312::1) ",
        "2001:3e8:0:313::1 ":"313--.fp1 (2001:3e8:0:313::1) ",
        "2001:3e8:0:314::1 ":"314--threatarmor-backup.fp1 (2001:3e8:0:314::1) ",
        "2001:3e8:0:315::1 ":"315--fg6300f.fp1 (2001:3e8:0:315::1) ",
        "2001:3e8:0:316::1 ":"316--.fp1 (2001:3e8:0:316::1) ",
        "2001:3e8:0:317::1 ":"317--fg6300f-backup.fp1 (2001:3e8:0:317::1) ",
        "2001:3e8:0:321::1 ":"321--th7740cfw-1.fp2 (2001:3e8:0:321::1) ",
        "2001:3e8:0:322::1 ":"322--th7740cfw-1.fp2 (2001:3e8:0:322::1) ",
        "2001:3e8:0:323::1 ":"323--th7740cfw-2.fp2 (2001:3e8:0:323::1) ",
        "2001:3e8:0:324::1 ":"324--th7740cfw-2.fp2 (2001:3e8:0:324::1) ",
        "2001:3e8:0:328::1 ":"328--pa5280.fp2 (2001:3e8:0:328::1) ",
        "2001:3e8:0:332::1 ":"332--pa5280-backup.fp2 (2001:3e8:0:332::1) ",
        "2001:3e8:0:330::1 ":"330--pa5280-captive.fp2 (2001:3e8:0:330::1) ",
        "2001:3e8:0:333::1 ":"333--pa5280-captive-backup.fp2 (2001:3e8:0:333::1) ",
        "2001:3e8:0:334::1 ":"334--s4048on.fp2 (2001:3e8:0:334::1) ",
        "2001:3e8:0:336::1 ":"336--s4048on-backup.fp2 (2001:3e8:0:336::1) ",
    }

    newtext = ''
    for line in text.splitlines():
        for (ip, host) in convert_dict.items():
            line = line.replace(ip, host)
        newtext += line + '\n'

    return newtext


## Basic tests before starting multiple test

def check_wifi_down():
    all_down = True
    for wifi in wifi_list:
        output = subprocess.check_output(['ifconfig', wifi]).decode()
        if 'status: active' in output:
            print('wifi "{}" might be active. Please stop it first.'.format(wifi))
            all_down = False
    return all_down

def check_nics():
    for nic in nic_list:
        output = subprocess.check_output(['ifconfig', nic]).decode()
        for line in output.splitlines():
            flag_print = False
            if 'mtu' in line: flag_print = True
            if 'inet' in line: flag_print = True
            if 'inet6' in line: flag_print = True
            if 'status' in line: flag_print = True
            if 'vlan' in line: flag_print = True
            if 'parent' in line: flag_print = True
            if flag_print:
                print(line)
        print()

def check_default_route():
    (stdout_data, stdout_err) = get_pipe_command_result('netstat -rn | grep default')
    text = ''
    gateways = []
    for line in stdout_data.splitlines():
        words = line.split()
        intf = words[-1]
        if intf not in nic_list:
            continue
        gateways.append(words[1])
        text += line + '\n'
    print(text)

    counter = 0
    for gateway in gateways:
        print(gateway)
        if '.' in gateway:
            #ipv4 : address syntax X.X.X.X
            for size in PINGV4_GATEWAY_SIZE_LIST:
                command = 'ping -c 3 -D -s {} {}  2>&1 | cat'.format(size, gateway)
                command_thread = AsyncCommandCaller(counter, command)
                command_thread.start()
                command_threads.append(command_thread)
                counter += 1
                time.sleep(SLEEP_TIME)

        elif ':' in gateway:
            #ipv6 : address syntax X:X::X:X
            for size in PINGV6_GATEWAY_SIZE_LIST:
                command = 'ping6 -c 3 -D -s {} {}  2>&1 | cat'.format(size, gateway)
                command_thread = AsyncCommandCaller(counter, command)
                command_thread.start()
                command_threads.append(command_thread)
                counter += 1
                time.sleep(SLEEP_TIME)

        else:
            # should not happen
            pass


## Threading tests base.

class AsyncCommandCaller(threading.Thread):
    def __init__(self, counter, command, decorator=None):
        super(AsyncCommandCaller, self).__init__()
        self.counter = counter
        self.command = command
        self.decorator = decorator
        self.thread = threading.Thread(target=self.run)

    def run(self):
        proc = subprocess.Popen(self.command, shell=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout_data, stderr_data) = proc.communicate()
        output = stdout_data.decode()
        if self.decorator != None:
            output = self.decorator(output)
        text = '# {}\n\n{}\n=========\n'.format(self.command, output)
        sync_add_result(self.counter, text)

## Main

def _test():
    # Wifi check
    # - check status is not active
    print('CHECK WIFI')
    if check_wifi_down():
        print('INFO: all wifi interfaces are down.')
    else:
        print('ERROR: **ABORT** this program since wifi is active.')
        exit()
    print('\n=========\n')

    # Physical nic check:
    # - v4 address
    # - v6 address
    # - status
    # - vlan
    # - physical nic of vlan
    print('CHECK PHYSICAL NICS')
    check_nics()
    print('\n=========\n')

    # Default route check
    # - ipv4, ipv4 entries (netstat -rn | grep default)
    # - ping reachability (ping and ping6)
    print('CHECK DEFAULT ROUTE')
    check_default_route()
    print('\n=========\n')

    # Start multiple tests
    for counter, command in command_list:
        if 'mtr' in command:
            command_thread = AsyncCommandCaller(counter, command, convert_ip_to_host)
        elif 'traceroute' in command:
            command_thread = AsyncCommandCaller(counter, command, convert_ip_to_host)
        elif 'traceroute6' in command:
            command_thread = AsyncCommandCaller(counter, command, convert_ip_to_host)
        else:
            command_thread = AsyncCommandCaller(counter, command)
        command_thread.start()
        command_threads.append(command_thread)
        time.sleep(SLEEP_TIME)

    # Wait all threads
    for command_thread in command_threads:
        print('waiting command threads.... : "{}"'.format(command_thread.command))
        command_thread.join()
    print('\n\n=========\n')

    # Print command results with user defined order
    keys = list(result_dict.keys())
    keys.sort()
    for key in keys:
        print(result_dict[key])

if __name__ == '__main__':
    _test()
