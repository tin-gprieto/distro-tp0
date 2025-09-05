from asyncio import threads
import signal
import socket
import logging
import sys
import threading

from common.thread_pool import ThreadPool
from common.client_handler import ClientHandlerThread

class Server:
    def __init__(self, port, listen_backlog, client_amount):
        # Initialize server socket
        self.running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        # Initialize server state
        self.client_amount = int(client_amount)
        
        file_lock = threading.Lock()
        barrier = threading.Barrier(self.client_amount)

        threads = [ClientHandlerThread(i, file_lock, barrier) for i in range(self.client_amount)]

        self.thread_pool = ThreadPool(threads)

    def run(self):

        signal.signal(signal.SIGTERM, lambda signum, frame: (self.server_shutdown(), sys.exit(0)))

        self.thread_pool.start()
        
        while self.running:
            client_sock, ip = self.__accept_new_connection()
            self.thread_pool.assign_connection(client_sock, ip)
        
    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c, addr[0]
    
    def server_shutdown(self):
        logging.info("action: shutdown | result: in_progress")
        self.running = False
        self._server_socket.close()
        # Esperar a que terminen todos los hilos
        self.thread_pool.join()
        logging.info("action: shutdown | result: success")
        sys.exit(0)
