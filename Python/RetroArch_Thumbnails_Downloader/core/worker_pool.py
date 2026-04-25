from concurrent.futures import ThreadPoolExecutor

class WorkerPool:
    def __init__(self, max_workers=5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def map(self, func, items):
        if not items:
            return []
        return list(self.executor.map(func, items))
    
    def close(self):
        self.executor.shutdown(wait=True)
