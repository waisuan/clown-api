import threading, ctypes, time, helpr, queue


class Cleanr(threading.Thread):
    def __init__(self, dir):
        threading.Thread.__init__(self)
        self.dir = dir
        self.queue = queue.Queue()

    def run(self):
        try:
            while True:
                if not self.queue.empty():
                    try:
                        file_to_delete = self.queue.get()
                        print("Purging..." + file_to_delete)
                        helpr.purge_file(self.dir, file_to_delete)
                    except:
                        print("Failed to purge. Will try again later.")
                time.sleep(15)  # X sec
        finally:
            pass

    def add_to_queue(self, filename):
        self.queue.put(filename)

    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        thread_id = self.get_id()
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                   ctypes.py_object(SystemExit))


