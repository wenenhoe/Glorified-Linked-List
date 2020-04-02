import socket
import queue
from threading import Thread
import sys

NODE_IP_LIST = ["127.0.0.1", "127.0.0.2", "127.0.0.3"]
NNODE = len(NODE_IP_LIST)
PORT_NUMBER = 4004

MSG_QUEUE = [queue.Queue() for i in range(NNODE)]
INPUT = ""

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


def comm_thread_fn(node_index):
    
    global INPUT
    
    ip_addr = NODE_IP_LIST[node_index]
    client_socket = init_client_socket(ip_addr)
    
    msg_queue = MSG_QUEUE[node_index]
    
    while True:
        
        if INPUT != "":
            client_socket.sendall(INPUT.encode('utf-8'))
            INPUT = ""
            
        if not msg_queue.empty():
            print("\n{}: {}\nInput: ".format(ip_addr, msg_queue.get()), end="")
            
def listen_thread_fn(sock):
    
    def recv_data(conn, addr):
        
        index = NODE_IP_LIST.index(addr[0])
        
        while True:
            try:
                data = conn.recv(1024)
                if data:
                    
                    data = data.decode('utf-8')
                    
                    MSG_QUEUE[index].put(data)
                        
                else:
                    pass
            except:
                conn.close()
                return False
    
    while True:
        conn, addr = sock.accept()
        Thread(target = recv_data, args = (conn, addr)).start()
        
def input_thread():
    global INPUT
  
    while True:
        INPUT = input("Input: ")
        
def main():
    
    global OWN_IP
    global NODE_INDEX
    NODE_INDEX = int(sys.argv[1])
    OWN_IP = NODE_IP_LIST[NODE_INDEX]
    
    print("[*] Initialising {}".format(OWN_IP))
    
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
    
    input_thread()
        
if __name__ == "__main__":  
    main()