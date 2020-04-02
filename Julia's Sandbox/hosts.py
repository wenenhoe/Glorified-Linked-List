NODE_IP_LIST = ["127.0.0.1", "127.0.0.2", "127.0.0.3"]
NODE_NAME_LIST = ["Host 1", "Host 2", "Host 3"]

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
    
    details = {}
    details['ip'] = ip
    details['isonline'] = False
    
    node = {}
    node['name'] = name    
    node['details'] = details
    
    return node