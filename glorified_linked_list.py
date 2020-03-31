import threading
import queue
import socket
import json
import uuid
import re

BUFFER_SIZE = 1024
PORT_NUMBER = 4004

node_ip_list = ["192.168.0.1", "192.168.0.2", "192.168.0.3"]
is_node_online_list = [["Host A", False], ["Host B", False], ["Host C", False]]

#blockchain_struct = ??  # TO BE INITIALISED
blockchain_queue = queue.Queue()
recycle_queue = queue.Queue()
reply_queue_tb = [None, None, None]
blkchn_thread_lock = threading.Lock()

is_update_online_list = False
is_update_blockchain = False
broadcast_flag = 0


def init_socket(ip_addr):
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for attempt in range(3):
        socket_client.settimeout(1)
        try:
            socket_client.connect((ip_addr, PORT_NUMBER))
            
        except socket.timeout:
            pass
        else:
            return socket_client
    return 0    


def get_and_format_mac():
    mac_addr_string = hex(uuid.getnode())[2:]
    mac_addr_split = re.findall("..", mac_addr_string)
    mac_addr = ":".join(mac_addr_split)
    return mac_addr


def format_json_str(json_str):
    formatted_data = json.loads(json_str)
    return formatted_data


def transfer_control():
    if not blkchn_thread_lock.locked():
        blkchn_thread_lock.acquire()
    else:
        while True:
            if blkchn_thread_lock.locked():
                time.sleep(random.random())
            else:
                blkchn_thread_lock.acquire()


def comm_thread_fn(own_mac_addr, ip_addr, node_name, node_index):
    client_socket = init_socket(ip_addr)
    if not client_socket:
        return 0
    
    while True:
        json_data = client_socket.recv(1024)
        str_data = format_json_str()
        data_type = 
        
        if broadcast_flag != "":
            to_send_dict = dict()
            to_send_dict["type"] = broadcast_flag
            to_send_dict["sender_mac"] = own_mac_addr
            to_send_dict["receiver_mac"] = "FF:FF:FF:FF:FF:FF"
            
            if broadcast_flag == "UpdateGOL":
                to_send_dict["GOL"] = is_node_online_list
            elif broadcast_flag == "UpdateChain Request" or broadcast_flag == "UpdateChain Reply":
                to_send_dict["chain"] = blockchain_struct

            client_socket.send(json.dumps(to_send_dict))
            broadcast_flag = ""

        if str_data["type"] == "Hello Request":
            node_dict[node_name] = True
            receiver_mac = str_data["sender_mac"]
            
            hello_reply_dict = dict()
            hello_reply_dict["type"] = "Hello Reply"
            hello_reply_dict["sender_mac"] = own_mac_addr
            hello_reply_dict["receiver_mac"] = receiver_mac
            client_socket.send(json.dumps(hello_reply_dict))            

        elif str_data["type"] == "UpdateGOL":
            is_update_online_list = True
            transfer_control()

        elif str_data["type"] == "UpdateChain Request":
            node_dict[node_name] = True
            receiver_mac = str_data["sender_mac"]
            
            update_chain_reply_dict = dict()
            update_chain_reply_dict["type"] = "UpdateChain Reply"
            update_chain_reply_dict["sender_mac"] = own_mac_addr
            update_chain_reply_dict["receiver_mac"] = ""
            update_chain_reply_dict["chain"] = blockchain_struct
            client_socket.send(json.dumps(update_chain_reply_dict)) 

        elif str_data["type"] == "UpdateChain Reply":
            reply_queue_tb[node_index] = None
            node_dict[node_name] = True
            is_update_blockchain = True
            reply_queue_tb[node_index] = str_data["chain"]
            transfer_control()
            


def blkchn_thread_fn(): # TO BE INITIALISED
    blkchn_thread_lock.release()    # To release upon finish execution


def main():
    own_mac_addr = get_and_format_mac()
    node_comm_thread_list = []

    while True:
        for index in range(len(is_node_online_list)):
            node_name = is_node_online_list[index][0]
            comm_thread = threading.Thread(target=comm_thread_fn, args=((own_mac_addr, node_ip_list, node_name, index)))
            comm_thread.start()
            node_comm_thread_list.append(comm_thread)
            
        blkchn_thread = threading.Thread(target=blkchn_thread_fn, args=((,)))       # TO BE INITIALISED
    


if __name__ == "__main__":
    main()
