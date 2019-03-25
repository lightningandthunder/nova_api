import threading
from functools import wraps

class LibThreadManager:
    def __init__(self):
        self.lock = threading.Lock()

    def _cmd(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                func(*args, **kwargs)

        return wrapper

    def start_thread(self, func, *args):
        t = self.Thread(self._cmd, func, args)

    class Thread(threading.Thread):
        def __init__(self, t, *args):
            threading.Thread.__init__(self, target=t, args=args)
            self.start()