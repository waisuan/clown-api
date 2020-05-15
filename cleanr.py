import threading, ctypes, time, helpr, queue
from modules.user import user

queue = queue.Queue()


class Cleanr(threading.Thread):
    _instance = None

    def __init__(self, dir='./static'):
        threading.Thread.__init__(self)
        self.dir = dir
        self.halt = False

    def run(self):
        try:
            while not self.halt:
                # Look for stale static files to purge.
                while not queue.empty():
                    try:
                        file_to_delete = queue.get()
                        print("Purging..." + file_to_delete)
                        helpr.purge_file(self.dir, file_to_delete)
                    except:
                        print("Failed to purge. Will try again later.")
                # Look for stale users to purge.
                user.user_store.purgeStaleUsers()
                time.sleep(3600)
        finally:
            pass

    def stop(self):
        self.halt = True
