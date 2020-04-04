class RecycleBlock:
    def __init__(self, data, timestamp, n_nodes):
        self.data = data
        self.timestamp = timestamp
        self.status = [False]*n_nodes