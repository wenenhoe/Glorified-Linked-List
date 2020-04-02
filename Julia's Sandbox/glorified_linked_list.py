import threading
import queue
import socket
import json

from messages import *
from hosts import *

HOST_NO = 0

BUFFER_SIZE = 1024
PORT_NUMBER = 4004 # Port to listen to

NODES_LIST = [init_node(ip, name) for ip,name in zip(NODE_IP_LIST, NODE_NAME_LIST)]
N_NODES = len(NODES_LIST)

OWN_NODE = node_list[HOST_NO]
OWN_NAME = OWN_NODE['details']['name']
OWN_IP = OWN_NODE['details']['ip']

BLOCKCHAIN = [] # TODO
BLOCKCHAIN_QUEUE = queue.Queue()
RECYCLE_QUEUE = queue.Queue()
BLKCHN_THREAD_LOCK = threading.Lock()

# Flags
BROADCAST_FLAG = [None]*N_NODES

def init_server_sock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((OWN_IP, PORT_NUMBER))
    sock.listen()
    return sock

def init_client_socket(ip_addr):
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        socket_client.settimeout(1)
        try:
            socket_client.connect((ip_addr, PORT_NUMBER))
            
        except socket.timeout:
            pass
        else:
            return socket_client
    return 0    

def mod_global_sync(flag, chain = None, nodes = None):
    
    BLKCHN_THREAD_LOCK.acquire()
    mod_globals_fn(flag, chain = chain, nodes = nodes)
    BLKCHN_THREAD_LOCK.release()


def comm_thread_fn(node_index):
    
    node = NODES_LIST[node_index]
    name = node['name']
    ip_addr = node['details']['ip']
    
    client_socket = init_client_socket(ip_addr)
    server_socket = init_server_sock()
    
    while True:
        
        msg = RecvMsg(server_socket)
        
        if BROADCAST_FLAG[node_index] != "":
            
            msgtype = BROADCAST_FLAG[node_index]
            header = ConstructHeader(OWN_IP, OWN_NAME, ip_addr, name)
            SendMsgType(client_socket, msgtype, header, chain = BLOCKCHAIN, nodes = NODES_LIST)

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
            

def mod_globals_fn(flag, chain = None, nodes = None): 
    return

def main():

    while True:
        for index in range(len(is_node_online_list)):
            node_name = is_node_online_list[index][0]
            comm_thread = threading.Thread(target=comm_thread_fn, args=((own_mac_addr, node_ip_list, node_name, index)))
            comm_thread.start()
            node_comm_thread_list.append(comm_thread)
            
        blkchn_thread = threading.Thread(target=blkchn_thread_fn, args=((,)))       # TO BE INITIALISED
    


if __name__ == "__main__":
    main()
