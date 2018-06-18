from flask import *
import json
import subprocess
import re

IP = '0.0.0.0'
PORT = 80
MTR_PATTERN = re.compile(r'^\d')

HELP = '''API Format
http://SERVER_IP:PORT/
http://SERVER_IP:PORT/api/v1/help
Provide help


http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/<TEST_NAME>
<NIC_NAME>: eth0 etc
<VLAN_ID>: '0' means no tag
<TEST_NAME>: Name of tests. Please read below


TESTS. Supports only GET method.

http://SERVER_IP:PORT/api/v1/interfaces
get list of interfaces which includes both physical and vlan(sub-interface)

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/ipv4
get IPv4 address and mask on the interface

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/ipv6
get IPv6 address and prefix on the interface

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/gatewayv4
get IPv4 gateway address

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/gatewayv6
get IPv6 gateway address

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/pingv4/<TARGET>
get ping v4 result to the target

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/pingv6/<TARGET>
get ping v6 result to the target

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/mtrv4/<TARGET>
get mtr v4 result to the target

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/mtrv6/<TARGET>
get mtr v6 result to the target

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/digv4/<TARGET>
get dig v4 result to the target

http://SERVER_IP:PORT/api/v1/<NIC_NAME>/vlan/<VLAN_ID>/digv6/<TARGET>
get dig v6 result to the target
'''

## HELP

app = Flask(__name__)
@app.route('/', methods=['GET'])
def api_root():
    return api_help()

@app.route('/api/v1/', methods=['GET'])
def api_apiroot():
    return api_help()

@app.route('/api/v1/help', methods=['GET'])
def api_help():
    return Response(HELP, mimetype='text/plain')


# IP ADDRESS

@app.route('/api/v1/interfaces', methods=['GET'])
def api_interfaces():
    def get_interfaces(output):
        interfaces = []
        for line in output.splitlines():
            if 'mtu' not in line:
                continue
            intf = line.split()[0] # eth0:
            intf = intf[:-1] # remove last :
            interfaces.append(intf)
        return interfaces

    command = 'ifconfig'
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'interfaces':get_interfaces(stdout)
        }
    }
    return make_response(jsonify(result), 200)

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/ipv4', methods=['GET'])
def api_ipv4(nic, vlan):
    def get_ipv4(output):
        ips = []
        for line in output.splitlines():
            if 'inet ' not in line:
                continue
            words = line.split()
            ip = words[1]
            mask = words[3]
            ips.append([ip, mask])
        return ips

    intf = nic
    if vlan != '0':
        intf = '{}.{}'.format(intf, vlan)
    command = 'ifconfig {}'.format(intf)
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'ipv4':get_ipv4(stdout),
        }
    }
    return make_response(jsonify(result), 200)


@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/ipv6', methods=['GET'])
def api_ipv6(nic, vlan):
    def get_ipv6(output):
        ips = []
        for line in output.splitlines():
            if 'inet6 ' not in line:
                continue
            words = line.split()
            ip = words[1]
            prefixlen = words[3]
            ips.append([ip, prefixlen])
        return ips

    intf = nic
    if vlan != '0':
        intf = '{}.{}'.format(intf, vlan)
    command = 'ifconfig {}'.format(intf)
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'ipv6':get_ipv6(stdout),
        }
    }
    return make_response(jsonify(result), 200)


# Gateway

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/gatewayv4', methods=['GET'])
def api_gatewayv4(nic, vlan):
    def get_gatewayv4(output, intf):
        for line in output.splitlines():
            if 'default' not in line:
                continue
            if intf not in line:
                continue
            words = line.split()
            return words[1]
        return ''

    intf = nic
    if vlan != '0':
        intf = '{}.{}'.format(intf, vlan)
    command = 'route'
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'gatewayv4':get_gatewayv4(stdout, intf)
        }
    }
    return make_response(jsonify(result), 200)

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/gatewayv6', methods=['GET'])
def api_gatewayv6(nic, vlan):
    def get_gatewayv6(output, intf):
        for line in output.splitlines():
            if 'UG' not in line:
                continue
            if intf not in line:
                continue
            words = line.split()
            return words[1]
        return ''

    intf = nic
    if vlan != '0':
        intf = '{}.{}'.format(intf, vlan)
    command = 'route -6'.format(intf)
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'gatewayv6':get_gatewayv6(stdout, intf)
        }
    }
    return make_response(jsonify(result), 200)


# ping

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/pingv4/<string:target>', methods=['GET'])
def api_pingv4(nic, vlan, target):
    def get_pingv4_result(output):
        for line in output.splitlines():
            if 'packets transmitted' not in line:
                continue
            words = line.split()
            send = words[0]
            receive = words[3]
            loss_rate = words[5]
            return (send, receive, loss_rate)
        return ('', '', '')

    intf = nic
    if vlan != '0':
        intf = '{}.{}'.format(intf, vlan)
    size = 1472
    command = 'ping -I {} -c 3 -D -s {} {}  2>&1 | cat'.format(intf, size, target)
    #command = 'ping -c 3 -D -s {} {}  2>&1 | cat'.format(size, target)
    (stdout, stderr) = get_pipe_command_result(command)
    (send, receive, loss_rate) = get_pingv4_result(stdout)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'send':send,
            'receive':receive,
            'loss_rate':loss_rate
        }
    }
    return make_response(jsonify(result), 200)

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/pingv6/<string:target>', methods=['GET'])
def api_pingv6(nic, vlan, target):
    def get_pingv6_result(output):
        for line in output.splitlines():
            if 'packets transmitted' not in line:
                continue
            words = line.split()
            send = words[0]
            receive = words[3]
            loss_rate = words[5]
            return (send, receive, loss_rate)
        return ('', '', '')

    intf = nic
    if vlan != '0':
        intf = '{}.{}'.format(intf, vlan)
    size = 1232
    command = 'ping6 -I {} -c 3 -D -s {} {}  2>&1 | cat'.format(intf, size, target)
    (stdout, stderr) = get_pipe_command_result(command)
    (send, receive, loss_rate) = get_pingv6_result(stdout)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'send':send,
            'receive':receive,
            'loss_rate':loss_rate
        }
    }
    return make_response(jsonify(result), 200)



# MTR

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/mtrv4/<string:target>', methods=['GET'])
def api_mtrv4(nic, vlan, target):
    def get_mtrv4_result(output):
        hops = []
        for line in output.splitlines():
            line = line.strip()
            match = MTR_PATTERN.search(line)
            if match is None:
                continue
            words = line.split()
            if len(words) >= 1:
                hops.append(words[1])
        return hops

    command = 'mtr -n -c 100 -i 0.1 -wb --report {} 2>&1 | cat'.format(target)
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'hops_ip':get_mtrv4_result(stdout),
        }
    }
    return make_response(jsonify(result), 200)

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/mtrv6/<string:target>', methods=['GET'])
def api_mtrv6(nic, vlan, target):
    def get_mtrv6_result(output):
        hops = []
        for line in output.splitlines():
            line = line.strip()
            match = MTR_PATTERN.search(line)
            if match is None:
                continue
            words = line.split()
            if len(words) >= 1:
                hops.append(words[1])
        return hops

    command = 'mtr -6 -n -c 100 -i 0.1 -wb --report {} 2>&1 | cat'.format(target)
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'hops_ip':get_mtrv6_result(stdout),
        }
    }
    return make_response(jsonify(result), 200)


# DIG

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/digv4/<string:target>', methods=['GET'])
def api_digv4(nic, vlan, target):
    command = 'dig +short {} 2>&1 | cat'.format(target)
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'ipv4':stdout.strip()
        }
    }
    return make_response(jsonify(result), 200)

@app.route('/api/v1/<string:nic>/vlan/<string:vlan>/digv6/<string:target>', methods=['GET'])
def api_digv6(nic, vlan, target):
    command = 'dig +short {} AAAA 2>&1 | cat'.format(target)
    (stdout, stderr) = get_pipe_command_result(command)

    result = {
        'result':True,
        'data':{
            'command':command,
            'stdout':stdout,
            'stderr':stderr,
            'ipv6':stdout.strip()
        }
    }
    return make_response(jsonify(result), 200)

## UTIL

def get_pipe_command_result(command):
    proc = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout_data, stderr_data) = proc.communicate()
    return (stdout_data.decode(), stderr_data.decode())

if __name__ == '__main__':
    app.debug = True
    app.run(host=IP, port=PORT, threaded=True)
