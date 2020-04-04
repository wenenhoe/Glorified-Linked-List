import hashlib
import datetime
import pickle


class Block:
    def __init__(self, data, previous_hash, previous_block):
        if previous_block == None:
            self.timestamp = datetime.datetime(2009, 1, 3, 17, 15)
        else:
            self.timestamp = datetime.datetime.utcnow()
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.generate_hash()
        self.previous_block = previous_block

    def generate_hash(self):
        data_to_hash = self.format_datetime() + self.data + self.previous_hash
        hash_hexdigest = hashlib.sha256(data_to_hash.encode("utf-8")).hexdigest()
        return hash_hexdigest

    def format_datetime(self):
        return self.timestamp.strftime("%c")


class Blockchain:
    def __init__(self):
        self.latest_block = Block("The Times 03/Jan/2009 Chancellor on brink of second bailout for banks", "0", None)
        self.chain_length = 1

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
    
    def add_block(self, data):
        if self.verify_chain():
            new_block = Block(data, self.latest_block.generate_hash(), self.latest_block)
            self.latest_block = new_block
            self.chain_length += 1
            return True
        return False


def is_current_chain_dropped(curr_chain, new_chain):
    if curr_chain.verify_chain() and new_chain.verify_chain():
        if curr_chain.chain_length < new_chain.chain_length:
            curr_chain.latest_block = new_chain.latest_block
            return True
        if curr_chain.chain_length == new_chain.chain_length:
            if curr_chain.latest_block.hash < new_chain.latest_block.hash:
                curr_chain.latest_block = new_chain.latest_block
                return True
    return False
        

def object_to_bytes_array(obj): # To store Blockchain object as bytes_array
    return pickle.dumps(obj)


def bytes_array_to_object(bytes_arr): # To load bytes_array as Blockchain object
    return pickle.loads(bytes_arr)
