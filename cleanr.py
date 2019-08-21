import threading, ctypes, time, helpr, queue


class Cleanr(threading.Thread):
    def __init__(self, dir):
        threading.Thread.__init__(self)
        self.dir = dir
        self.queue = queue.Queue()
        self.halt = False

    def run(self):
        try:
            while not self.halt:
                if not self.queue.empty():
                    try:
                        file_to_delete = self.queue.get()
                        print("Purging..." + file_to_delete)
                        helpr.purge_file(self.dir, file_to_delete)
                    except:
                        print("Failed to purge. Will try again later.")
                time.sleep(60)  # X sec
        finally:
            pass

    def add_to_queue(self, filename):
        self.queue.put(filename)

    def stop(self):
        self.halt = True

