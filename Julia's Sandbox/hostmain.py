# Contains the code that runs the blockchain host
# Takes in argument n (int) that indicates the host's index
# (List of hosts contained in hosts.py)
# ~ JuliaPoo

import queue
import socket
import json
import sys
import time
import warnings
import datetime
import threading
from threading import Thread
import traceback

from messages import *
from hosts import *
from blockchain import *
from recycle import *

# To support large chain lengths
# This is generally not a good idea due to python's being inefficient with the stack
# but it is a quick fix.
sys.setrecursionlimit(100000)

BUFFER_SIZE = 10000
PORT_NUMBER = 4004 # Port to listen to

# Network info
NODES_LIST = [init_node(ip, name) for ip,name in zip(NODE_IP_LIST, NODE_NAME_LIST)]
N_NODES = len(NODES_LIST)

# Global structs
BLOCKCHAIN = Blockchain()
BLOCKCHAIN_QUEUE = queue.Queue()
RECYCLE_QUEUE = []
INPUT_QUEUE = queue.Queue()
MSG_QUEUE = [queue.Queue() for i in range(N_NODES)]
BROADCAST_QUEUE = [queue.Queue() for i in range(N_NODES)]
MOD_GLOBAL_LOCK = threading.Lock()

# Online status
OWN_STATUS = True

def init_server_sock():
    
    '''
    Initialises the listening socket
    
    returns listening socket (socket.Socket obj)
    '''
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((OWN_IP, PORT_NUMBER))
    sock.listen()
    return sock

def init_client_socket(ip_addr):
    
    '''
    Initialises connection socket
    ip_addr: string, ip of host to connect to
    
    returns connection socket (socket.Socket obj)
    '''
    
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
    
    '''
    Listening Thread that spawns more threads for each connection established
        For each host it listens data to, it adds to the message queue of the
        communicating thread of said host to respond to the message.
    
    sock: Listening socket (socket.Socket obj)
    '''
    
    def recv_data(conn, addr):
        index = NODE_IP_LIST.index(addr[0])      
        while True:
            try:
                all_data = b""
                while True:
                    data = conn.recv(BUFFER_SIZE)
                    if data:
                        all_data += data
                        idx = data.find(ENDBYTES.encode('utf-8'))
                        if idx != -1:
                            data_split = all_data.split(ENDBYTES.encode('utf-8'))
                            all_data = data_split[-1]
                            for d in data_split:
                                if len(d) == 0: continue
                                msg = StrToMsg(d)
                                MSG_QUEUE[index].put(msg)
                            break
                    else:
                        pass
            except Exception as e:
                print(e)
                traceback.print_exc()
                conn.close()
                return False
            
    while True:
        conn, addr = sock.accept()
        print("[*] Accepting data from {}\n".format(addr), end="")
        Thread(target = recv_data, args = (conn, addr)).start()

        
def mod_global_sync(flag, chain = None, nodes = None, data = None, timestamp = None, host = None):
    
    '''
    Wrapper for mod_globals_fn but with a lock so 
    only 1 thread can run mod_globals_fnat the same time
    
    Reason for this wrapper is that the operations of
    mod_global_sync is not thread safe.
    
    Thread safe operations of globals are instead put into comm_thread_fn for efficiency 
    '''
    
    MOD_GLOBAL_LOCK.acquire()
    mod_globals_fn(flag, chain = chain, nodes = nodes, data = data, timestamp = timestamp, host = host)
    MOD_GLOBAL_LOCK.release()
    
def mod_globals_fn(flag, chain = None, nodes = None, data = None, timestamp = None, host = None): 
    
    '''
    Modifies global variables NODES_LIST, BLOCKCHAIN, RECYCLE_QUEUE
    
    flag:
        "UPDATE NODES": 
            UpdateGol msg received, replace NODES with nodes data in msg
        "UPDATE BLKCHN": 
            Chain received from other hosts. Update own blockchain accordingly
                Use is_current_chain_dropped to determine if to keep own chain
                Update recycle queue accordingly [*]
        "ADD_BLOCK":
            Adds block to chain, recycle queue and broadcast change
    chain:
        Chain from message. (Block obj)
        Used only in "UPDATE BLKCHN"
    nodes:
        nodes information from message
        Used only in "UPDATE BLKCHN"
    timestamp:
        timestamp of new block (datetime obj)
        Used only in "ADD_BLOCK"
    data:
        data of new block
        Used only in "ADD_BLOCK"
    host:
        host that sent the msg.
        Used only in "UPDATE BLKCHN"
    
                
    [*]
    for each block in recycle queue, 
        if all node's chain has said block, remove from queue
        if all node's chain doesn't have said block, 
        add back to Blockchain and broadcast change
    '''
    
    global NODES_LIST
    global BLOCKCHAIN
    global RECYCLE_QUEUE
    
    chain = Blockchain(load_object = chain)
    
    if flag == "UPDATE NODES":
        if nodes == None: warnings.warn("nodes is None, provided flag might be wrong")
        NODES_LIST = nodes
        
    if flag == "UPDATE BLKCHN":
        if chain == None: warnings.warn("chain is None, provided flag might be wrong")
        if host == None: warnings.warn("host is None, provided flag might be wrong")
       
        changed = is_current_chain_dropped(BLOCKCHAIN, chain)

        # Update recycle queue TODO
        for r in RECYCLE_QUEUE:
            if is_recycle_in_chain(chain, r):
                r.status[host] = True
            if is_recycle_in_chain(BLOCKCHAIN, r):
                r.status[HOST_NO] = True

        to_readd = []
        for idx, r in enumerate(RECYCLE_QUEUE):
            # Check if all nodes has given block
            n_has = sum([r.status[i] == NODES_LIST[i]['details']['isonline'] for i in range(N_NODES)])
            
            if n_has == N_NODES:
                RECYCLE_QUEUE[idx] == None
                
            if n_has == 0:
                to_readd.append(r)

        RECYCLE_QUEUE = [r for r in RECYCLE_QUEUE if r!=None]
        for r in to_readd:
            BLOCKCHAIN.add_block(r.data, r.timestamp)

        # If blockchain was changed
        if changed or (len(to_readd) != 0):
            for idx, q in enumerate(BROADCAST_QUEUE):
                if idx == host or idx == HOST_NO: continue
                q.put("UpdateChain Reply")
        
    if flag == "ADD_BLOCK":
        if data == None: warnings.warn("data is None, provided flag might be wrong")
        if timestamp == None: warnings.warn("timestamp is None, provided flag might be wrong")
        
        BLOCKCHAIN.add_block(data, timestamp)
        r = RecycleBlock(data, timestamp, N_NODES)
        RECYCLE_QUEUE.append(r)
        
        for idx, q in enumerate(BROADCAST_QUEUE):
            if idx == HOST_NO: continue
            q.put("UpdateChain Reply")
        
    return
     
def comm_thread_fn(node_index):
    
    '''
    Handles sending of messages to host specified by node_index
    Messages are received from a message queue.
    
    If received Hello Request:
        Update NODES
        Reply with Hello Reply
        
    if received UpdateGOL:
        replace NODES with node data in msg
        
    if received UpdateChain Request:
        Update NODES
        Reply with UpdateChain Reply
        
    if received UpdateChain Reply:
        Update NODES
        Update BLOCKCHAIN and RECYCLE_QUEUE
        
    In the event connection errors:
        Assume host is down and periodically send Hello Request
        
    '''
    
    node = NODES_LIST[node_index]
    name = node['name']
    ip_addr = node['details']['ip']
    
    client_socket = init_client_socket(ip_addr)
    
    msg_queue = MSG_QUEUE[node_index]
    broadcast_queue = BROADCAST_QUEUE[node_index]
    
    while True:
        
        try:
            if not broadcast_queue.empty():
                msgtype = broadcast_queue.get()
                header = ConstructHeader(OWN_IP, OWN_NAME, ip_addr, name)
                SendMsgType(client_socket, msgtype, header, chain = BLOCKCHAIN, nodes = NODES_LIST)

                
            if not msg_queue.empty():

                msg = msg_queue.get()
                print("{}: {}\n".format(ip_addr, msg['TYPE']), end="")
                
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
                    SendMsgType(client_socket, "UpdateChain Reply", header, chain=BLOCKCHAIN)
                    

                elif msg["TYPE"] == "UpdateChain Reply":
                    NODES_LIST[node_index]['details']['isonline'] = True
                    chain = msg["CHAIN"]
                    mod_global_sync("UPDATE BLKCHN", chain = chain, host = node_index)
              
                    
        except Exception as e:
            print(e)
            traceback.print_exc()
            
            client_socket = init_client_socket(ip_addr)
            
            NODES_LIST[node_index]['details']['isonline'] = False
            
            # Empty all broadcast
            while not broadcast_queue.empty():
                broadcast_queue.get()
                
            # Empty msg queue
            while not msg_queue.empty():
                msg_queue.get()
            
            broadcast_queue.put("Hello Request")
            time.sleep(10)
            
            

def host_init():
    
    '''
    Initialises host:
    
    Gets network status by broadcasting Hello Request
    Once obtained network status, broadcast UPDATE_GOL
    Gets latest chain by broadcasting UpdateChain Request
    '''

    global OWN_STATUS
    
    # Broadcast Hello Request to build knowledge of network
    print("[*] Collecting network status\n", end="")
    for idx, q in enumerate(BROADCAST_QUEUE):
        if idx == HOST_NO: continue
        q.put("Hello Request")
    time.sleep(10)
    
    # Determine if node is online
    isonline_count = sum([n['details']['isonline'] for n in NODES_LIST])
    if isonline_count < (N_NODES-1) // 2:
        print("[*] Offline. Moving to offline execution\n", end="")
        OWN_STATUS = False
        return False
    
    # Broadcast UpdateGOL to send nodes latest network state
    print("[*] Collecting network status\n", end="")
    for idx,q in enumerate(BROADCAST_QUEUE):
        idx == HOST_NO
        q.put("UpdateGOL")
    
    # Broadcast UpdateChain Request to retrieve latest chain
    print("[*] Retrieving latest chain\n", end="")
    for idx,q in enumerate(BROADCAST_QUEUE):
        idx == HOST_NO
        q.put("UpdateChain Request")
    time.sleep(10)
    
    return True
    
    
def periodic_threads():
    
    '''
    Thread responsible for periodic operations
    
    Every minute broadcast Hello Request to get network status
    Every 3 minutes broadcast UpdateChain Request to verify latest chain
    '''
    
    print("[*] Initialising periodic broadcast threads\n", end="")
    def broadcast_hello():
        while(True):
            
            if not OWN_STATUS: continue
                
            print("[*] Periodic: Broadcasting Hello Request\n", end="")
            for q in BROADCAST_QUEUE:
                q.put("Hello Request")
            time.sleep(60)
    
    def broadcast_updatechain():
        while(True):
            
            if not OWN_STATUS: continue
                
            print("[*] Periodic: Broadcasting UpdateChain Request\n", end="")
            for q in BROADCAST_QUEUE:
                q.put("UpdateChain Request")
            time.sleep(60*3)
            
    Thread(target = broadcast_hello).start()
    Thread(target = broadcast_updatechain).start()

def offline_thread():
    
    '''
    Thread that checks if own host is offline.
    If offline, periodically sends Hello Request
    Once online again, re-initialises hosts
    '''
    
    global OWN_STATUS
    
    while True:
        
        isonline_count = sum([n['details']['isonline'] for n in NODES_LIST])
        time.sleep(5)
        
        if isonline_count < (N_NODES-1) // 2:
            OWN_STATUS = False
        
        if OWN_STATUS: continue
        
        # Offline mode
        
        for q in BROADCAST_QUEUE:
            q.put("Hello Request")
        time.sleep(5)
        
        if isonline_count >= (N_NODES-1) // 2:
            print("[*] Online. Reverting to online execution\n", end="")
            host_init()
            OWN_STATUS = True
    
def input_thread():
    
    '''
    Thread that takes user input.
    
    If input = "print status":
        prints network status
    if input = "print chain":
        prints contents of own chain
    if input = "query timestamp <timestamp>":
        retrieves all entries in chain with timestamp
    '''
    
    time.sleep(5)
    
    print ('''

***************************************
************* INITIALISED *************
***************************************


''', end = "")
    
    while True:
        data = input("Input:\n")
        
        if data == "print status":
            print("\n\nNODES:\n{}\n\n".format("\n".join([str((n['name'], n['details']['ip'], n['details']['isonline'])) for n in NODES_LIST])))
            continue
        elif data == "print chain":
            b = BLOCKCHAIN.latest_block
            chain = []
            while (b != None):
                chain = ["{}: {}".format(b.timestamp.strftime('%m-%d-%Y %H:%M'), b.data)] + chain
                b = b.previous_block
            print("\n\nCHAIN:\n{}\n\n".format("\n".join(chain)))
            continue
        elif data[:15] == "query timestamp":
            try:
                date = datetime.datetime.strptime(data[16:], '%m-%d-%Y %H:%M')
            except:
                print("Wrong datetime format. Format is {}\n".format("%m-%d-%Y %H:%M"), end="")
                continue
            results = query_blockchain(BLOCKCHAIN, date)
            print("\nRESULTS:\n{}\n\n".format("\n".join(["{}: {}".format(r.timestamp.strftime('%m-%d-%Y %H:%M'), r.data) for r in results])))
            continue
            
        
        mod_globals_fn("ADD_BLOCK", data = data, timestamp = datetime.datetime.utcnow())
                
def main():
    
    '''
    Initialises host and starts the threads.
    parent thread then becomes the input thread.
    '''
    
    global HOST_NO
    global OWN_NODE
    global OWN_NAME
    global OWN_IP
    
    HOST_NO = int(sys.argv[1])
    
    OWN_NODE = NODES_LIST[HOST_NO]
    OWN_NAME = OWN_NODE['name']
    OWN_IP = OWN_NODE['details']['ip']
    NODES_LIST[HOST_NO]['details']['isonline'] = OWN_STATUS
    
    print("[*] Initialising host {}\n".format(OWN_IP), end="")
    
    server_socket = init_server_sock()
    comm_threads = []
    
    for i in range(N_NODES):
        if i == HOST_NO: continue
        comm_threads.append(Thread(target=comm_thread_fn, args=(i,)))
    for thread in comm_threads:
        thread.start()
    print("[*] Initialised client threads\n", end="")
        
    server_thread = Thread(target = listen_thread_fn, args = (server_socket,)).start()
    print("[*] Initialised server threads\n", end="")
    
    host_init()
    periodic_threads()
    Thread(target = offline_thread).start()
    input_thread()
        
if __name__ == "__main__":  
    main()
    
    