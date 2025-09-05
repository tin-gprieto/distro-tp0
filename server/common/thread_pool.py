import logging
import threading


class ThreadPool:
    def __init__(self, threads):
        self.threads = threads
        self.lock = threading.Lock()
        self.by_ip = {}
        self.next = 0

    def assign_connection(self, client_socket, ip):
        if ip not in self.by_ip:
            self.by_ip[ip] = self.threads[self.next % len(self.threads)]
            self.next += 1
        thread = self.by_ip[ip]
        thread.assign_connection(client_socket, ip)

    def start(self):
        for thread in self.threads:
            thread.start()
        logging.debug("action: all_threads_started | result: success")

    def join(self):
        for thread in self.threads:
            thread.join()
        logging.debug("action: all_threads_finished | result: success")
            
    