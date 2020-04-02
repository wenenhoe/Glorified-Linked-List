import threading
import queue
import socket
import json
import sys
import time

from messages import *
from hosts import *

BUFFER_SIZE = 1024
PORT_NUMBER = 4004 # Port to listen to

# Network info
NODES_LIST = [init_node(ip, name) for ip,name in zip(NODE_IP_LIST, NODE_NAME_LIST)]
N_NODES = len(NODES_LIST)

# Global structs
BLOCKCHAIN = [] # TODO
BLOCKCHAIN_QUEUE = queue.Queue()
RECYCLE_QUEUE = queue.Queue()
MOD_GLOBAL_LOCK = threading.Lock()
MSG_QUEUE = [queue.Queue() for i in range(N_NODES)]
BROADCAST_QUEUE = [queue.Queue() for i in range(N_NODES)]

# Online status
OWN_STATUS = True

def init_server_sock():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((OWN_IP, PORT_NUMBER))
    sock.listen()
    return sock

def init_client_socket(ip_addr):
    
    while True:
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_client.bind((OWN_IP, 0))  # needed for loopback address
        try:
            socket_client.connect((ip_addr, PORT_NUMBER))   
        except:
            pass 
        else:
            return socket_client   
            
def listen_thread_fn(sock):
    
    def recv_data(conn, addr):
        index = NODE_IP_LIST.index(addr[0])      
        while True:
            try:
                data = conn.recv(1024)
                if data:
                    data = data.decode('utf-8')
                    msg = StrToMsg(data)
                    MSG_QUEUE[index].put(msg)        
                else:
                    pass
            except:
                conn.close()
                return False
            
    while True:
        conn, addr = sock.accept()
        Thread(target = recv_data, args = (conn, addr)).start()

        
def mod_global_sync(flag, chain = None, nodes = None):
    
    MOD_GLOBAL_LOCK.acquire()
    mod_globals_fn(flag, chain = chain, nodes = nodes)
    MOD_GLOBAL_LOCK.release()
    
def mod_globals_fn(flag, chain = None, nodes = None): 
    return
     
def comm_thread_fn(node_index):
    
    node = NODES_LIST[node_index]
    name = node['name']
    ip_addr = node['details']['ip']
    
    client_socket = init_client_socket(ip_addr)
    
    msg_queue = MSG_QUEUE[node_index]
    broadcast_queue = BROADCAST_QUEUE[node_index]
    
    while True:
        
        if not broadcast_queue.empty():
            
            msgtype = broadcast_queue.get()
            header = ConstructHeader(OWN_IP, OWN_NAME, ip_addr, name)
            SendMsgType(client_socket, msgtype, header, chain = BLOCKCHAIN, nodes = NODES_LIST)
            
        if not msg_queue.empty():
            
            msg = msg_queue.get()
            print("\n{}: {}\n".format(ip_addr, msg['TYPE']), end="")
            
            if msg["TYPE"] == "Hello Request":
                NODES_LIST[node_index]['details']['isonline'] = True
                header = ConstructHeader(OWN_IP, OWN_NAME, ip_addr, name)
                SendMsgType(client_socket, "Hello Reply", header)

            elif msg["TYPE"] == "UpdateGOL":
                gol = msg['GOL']
                mod_global_sync("UPDATE NODES", nodes = gol)

            elif msg["TYPE"] == "UpdateChain Request":
                NODES_LIST[node_index]['details']['isonline'] = True
                header = ConstructHeader(OWN_IP, OWN_NAME, ip_addr, name)
                SendMsgType(client_socket, "UpdateChain Reply", header)

            elif msg["TYPE"] == "UpdateChain Reply":
                NODES_LIST[node_index]['details']['isonline'] = True
                IS_UPDATE_BLKCHN = True
                chain = msg["CHAIN"]
                mod_global_sync("UPDATE BLKCHN", chain = chain)

def host_init():

    global OWN_STATUS
    
    # Broadcast Hello Request to build knowledge of network
    print("[*] Collecting network status")
    for q in BROADCAST_QUEUE:
        q.put("Hello Request")
    time.sleep(10)
    
    # Determine if node is online
    isonline_count = sum([n['details']['isonline'] for n in NODES_LIST])
    if isonline_count < (N_NODES-1) // 2:
        print("[*] Offline. Moving to offline execution")
        OWN_STATUS = False
        return False
    
    # Broadcast UpdateGOL to send nodes latest network state
    print("[*] Collecting network status")
    for q in BROADCAST_QUEUE:
        q.put("UpdateGOL")
    
    # Broadcast UpdateChain Request to retrieve latest chain
    print("[*] Retrieving latest chain")
    for q in BROADCAST_QUEUE:
        q.put("UpdateChain Request")
    time.sleep(10)
    
    return True
    
    
def periodic_threads():
    
    print("[*] Initialising periodic broadcast threads")
    def broadcast_hello():
        while(True):
            
            if not OWN_STATUS: continue
                
            print("[*] Periodic: Broadcasting Hello Request")
            for q in BROADCAST_QUEUE:
                q.put("Hello Request")
            time.sleep(60)
    
    def broadcast_updatechain():
        while(True):
            
            if not OWN_STATUS: continue
                
            print("[*] Periodic: Broadcasting UpdateChain Request")
            for q in BROADCAST_QUEUE:
                q.put("UpdateChain Request")
            time.sleep(60*3)
            
    Thread(target = broadcast_hello).start()
    Thread(target = broadcast_updatechain).start()

def offline_thread():
    
    global OWN_STATUS
    
    while True:
        
        if OWN_STATUS: continue
        
        # Offline mode
        
        for q in BROADCAST_QUEUE:
            q.put("Hello Request")
        time.sleep(5)

        isonline_count = sum([n['details']['isonline'] for n in NODES_LIST])
        if isonline_count >= (N_NODES-1) // 2:
            print("[*] Online. Reverting to online execution")
            OWN_STATUS = True
    

def input_thread():
    return
                
def main():
    
    global HOST_NO
    global OWN_NODE
    global OWN_IP
    
    HOST_NO = sys.argv[1]
    
    OWN_NODE = node_list[HOST_NO]
    OWN_NAME = OWN_NODE['details']['name']
    OWN_IP = OWN_NODE['details']['ip']
    NODES_LIST[HOST_NO]['details']['isonline'] = OWN_STATUS
    
    print("[*] Initialising host {}".format(OWN_IP))
    
    server_socket = init_server_sock()
    comm_threads = []
    
    for i in range(NNODE):
        if i == NODE_INDEX: continue
        comm_threads.append(Thread(target=comm_thread_fn, args=(i,)))
    for thread in comm_threads:
        thread.start()
    print("[*] Initialised client threads")
        
    server_thread = Thread(target = listen_thread_fn, args = (server_socket,)).start()
    print("[*] Initialised server threads")
    
    host_init()
    periodic_threads()
    Thread(target = offline_thread).start()
    # input_thread()
        
if __name__ == "__main__":  
    main()
    
    