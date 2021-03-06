# Messages are implemented as dictionary in Python and sent as a json string.
# Messages are in plaintext. Despite being inefficient, 
# the readability suffices for our proof-of-concept intentions

# Chains are pickle dumped base64 encoded strings. This allows chains to
# contain any sort of data.

# ~ wenenhoe

import json
import socket
import warnings

ENDBYTES = '\1'

def MsgToStr(msg): return json.dumps(msg)

def StrToMsg(_str):
    return json.loads(_str)

def SendMsg(sock, msg):
    msg_str = MsgToStr(msg) + ENDBYTES
    sock.sendall(msg_str.encode('utf-8'))

def SendMsgType(sock, msgtype, header, chain = None, nodes = None):
    
    print("[*] Sending msg of type {}".format(msgtype))
    
    if msgtype == 'Hello Request':
        msg = ConstructHelloRequests(header)
        
    if msgtype == 'Hello Reply':
        msg = ConstructHelloReply(header)
        
    if msgtype == 'UpdateChain Request':
        if chain == None: 
            warnings.warn("chain is None, provided msgtype might be wrong")
            
        msg = ConstructUpdateChainRequest(header, chain.object_to_str())
        
    if msgtype == 'UpdateChain Reply':
        if chain == None: 
            warnings.warn("chain is None, provided msgtype might be wrong")
        msg = ConstructUpdateChainReply(header, chain.object_to_str())
        
    if msgtype == "UpdateGOL":
        if nodes == None: 
            warnings.warn("nodes is None, provided msgtype might be wrong")
        msg = ConstructUpdateGOL(header, nodes)
        
    SendMsg(sock, msg)

def ConstructHeader(send_ip, send_name, recv_ip, recv_name):
    
    '''
    HEADER contains:
        Sender's IP
        Sender’s Name
        Receiver's IP
        Receiver's Name
    '''
    
    header = {}
    header['send_ip'] = send_ip
    header['send_name'] = send_name
    header['recv_ip'] = recv_ip
    header['recv_name'] = recv_name
    
    return header
    
def ConstructHelloRequests(header):
    
    '''
    Hello Requests contains:
        HEADER
        TYPE: "Hello Request"
    '''
        
    msg = {}
    msg['HEADER'] = header
    msg['TYPE'] = "Hello Request"
    
    return msg

def ConstructHelloReply(header):
    
    '''
    Hello reply contains:
        HEADER
        TYPE: "Hello Reply"
    '''
    
    msg = {}
    msg['HEADER'] = header
    msg['TYPE'] = "Hello Reply"
    
    return msg

def ConstructUpdateChainRequest(header, chain):
    
    '''
    UpdateChain Request contains:
        HEADER
        TYPE: "UpdateChain Request"
        Chain
    '''
    
    msg = {}
    msg['HEADER'] = header
    msg['TYPE'] = "UpdateChain Request"
    msg['CHAIN'] = chain
    
    return msg
    
def ConstructUpdateChainReply(header, chain):
    
    '''
    UpdateChain Request contains:
        HEADER
        TYPE: "UpdateChain Reply"
        Chain
    '''
    
    msg = {}
    msg['HEADER'] = header
    msg['TYPE'] = "UpdateChain Reply"
    msg['CHAIN'] = chain
    
    return msg
    
def ConstructUpdateGOL(header, nodes):
    
    '''
    UpdateGOL contains:
        HEADER
        TYPE: "UpdateGOL"
        GOL: NODES
    '''
    
    msg = {}
    msg['HEADER'] = header
    msg['TYPE'] = "UpdateGOL"
    msg['GOL'] = nodes
    
    return msg