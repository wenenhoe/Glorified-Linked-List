# Run this to run the demo
# Accepts an argument N (int) that generates N hosts

import os
from threading import Thread
import sys

ANACONDA = r'"cmd"'

HELP = '''
Usage: sys.argv[1] <n:int>
-- n: Number of hosts to generate
'''

# hosts.py script (Contains hosts information)
script = """
NODE_IP_LIST = {}
NODE_NAME_LIST = {}

def NodelistToGOL(nodelist): return json.dumps(nodelist)

def GOLToNodelist(GOL): return json.loads(GOL)

def init_node(ip, name):
    
    '''
    node contains:
        name
        details: 
            ip
            isonline: True if node is online and False otherwise
    '''
    
    details = {{}}
    details['ip'] = ip
    details['isonline'] = False
    
    node = {{}}
    node['name'] = name    
    node['details'] = details
    
    return node
"""
    
def main():
    global N_HOSTS
    global script
    
    if len(sys.argv) != 2:
        print (HELP)
    
    N_HOSTS = int(sys.argv[1])
    script = script.format(['127.0.0.{}'.format(i) for i in range(1, N_HOSTS+1)], 
                           ['Host {}'.format(i) for i in range(1, N_HOSTS+1)])
    
    with open("hosts.py", "w") as f:
        f.write(script)

    _exec = lambda cmd: os.system(cmd)

    for host_no in range(N_HOSTS):
        command = "start /wait {} python hostmain.py {}".format(ANACONDA, host_no)
        Thread(target=_exec, args=(command,)).start()
        
if __name__ == "__main__":
    main()