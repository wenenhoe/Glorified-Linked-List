import hashlib
import datetime
import pickle
import base64

class Block:
    def __init__(self, data, previous_hash, previous_block, timestamp):
        
        '''
        timestamp: datetime object of time input is made
        '''

        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.generate_hash()
        self.previous_block = previous_block

    def generate_hash(self):
        data_to_hash = self.timestamp.strftime("%c") + self.data + self.previous_hash
        hash_hexdigest = hashlib.sha256(data_to_hash.encode("utf-8")).hexdigest()
        return hash_hexdigest


class Blockchain:
    def __init__(self, latest_block=None, load_object=False):
        if latest_block == None:
            latest_block = Block("The Times 03/Jan/2009 Chancellor on brink of second bailout for banks", 
                                 "0", None, datetime.datetime(2009, 1, 3, 17, 15, 00))
        if load_object:
            latest_block = self.str_to_object(load_object)
        self.latest_block = latest_block


    def verify_genesis_block(self, block):
        if block.hash == block.generate_hash() and block.hash == 'e862806402a0a51a751f662ac110c936cee1838bb9d884e05bb26ce5704425cd':
            return True
        return False

    
    def verify_block(self, block):
        if block.previous_block == None:
            if self.verify_genesis_block(block):
                return True
        else:
            previous_block_generated_hash = block.previous_block.generate_hash()
            if block.previous_hash == previous_block_generated_hash and block.previous_block.hash == previous_block_generated_hash:
                return True
        return False


    def verify_chain(self):
        if self.latest_block.previous_block == None:
            if self.verify_genesis_block(self.latest_block):
                return True
            else: return False
        else:
            current_block = self.latest_block
            if current_block.hash == current_block.generate_hash():
                while current_block is not None:
                    if self.verify_block(current_block):
                        current_block = current_block.previous_block
                    else:
                        return False
                return True
        return False

    
    def add_block(self, data, timestamp):
        if self.verify_chain():
            new_block = Block(data, self.latest_block.generate_hash(), self.latest_block, timestamp)
            self.latest_block = new_block
            return True
        return False


    def object_to_str(self):
        return base64.b64encode(pickle.dumps(self.latest_block)).decode('utf-8')


    def str_to_object(self, _str):
        return pickle.loads(base64.b64decode(_str))
    

def get_chain_length(chain):
    
    length = 0
    ptr = chain.latest_block
    while ptr.previous_block != None:
        length += 1
        ptr = ptr.previous_block
    return length

def is_current_chain_dropped(curr_chain, new_chain):
    if curr_chain.verify_chain() and new_chain.verify_chain():
        clen = get_chain_length(curr_chain)
        nlen = get_chain_length(new_chain)
        if clen < nlen:
            curr_chain.latest_block = new_chain.latest_block
            return True
        if clen == nlen:
            if curr_chain.latest_block.hash < new_chain.latest_block.hash:
                curr_chain.latest_block = new_chain.latest_block
                return True
    return False

def is_recycle_in_chain(chain, r):
    ptr = chain.latest_block
    while ptr != None:
        if r.data == ptr.data and r.timestamp == ptr.timestamp:
            return True       
        ptr = ptr.previous_block
    return False

def query_blockchain(chain, datetime):
    results = []
    date = datetime.strftime('%m-%d-%Y %H:%M')
    ptr = chain.latest_block
    while ptr != None:
        if ptr.timestamp.strftime('%m-%d-%Y %H:%M') == date:
            results.append(ptr)
        ptr = ptr.previous_block
    return results