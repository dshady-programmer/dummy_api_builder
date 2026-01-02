from concurrent.futures import ThreadPoolExecutor
"""
Initialize a thread pool of max_workers of 5.

"""
executor = None 

def init_executor(max_workers=5):
    """
    Initialize the executor once and re-use throughout the process
    """
    global executor
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=max_workers)
    return executor