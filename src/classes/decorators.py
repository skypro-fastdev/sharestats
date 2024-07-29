import threading


def singleton(cls):
    """Singleton decorator"""
    instances = {}
    lock = threading.Lock()

    def get_instance(*args, **kwargs) -> object:
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]

    return get_instance
