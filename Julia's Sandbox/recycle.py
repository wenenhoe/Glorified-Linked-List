# JuliaPoo
class RecycleBlock:
    
    '''Class that is an element in the recycle queue'''
    
    def __init__(self, data, timestamp, n_nodes):
        
        '''
        data: Block data
        timestamp: Block timestamp (datetime obj)
        n_nodes: Number of hosts
        '''
        
        self.data = data
        self.timestamp = timestamp
        self.status = [False]*n_nodes