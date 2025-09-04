from asyncio import threads
import signal
import socket
import logging
import sys
import threading

from common.thread_pool import ThreadPool

class Server:
    def __init__(self, port, listen_backlog, client_amount):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        # Initialize server struct
        self.client_amount = int(client_amount)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        signal.signal(signal.SIGTERM, lambda signum, frame: (self.server_shutdown(), sys.exit(0)))

        file_lock = threading.Lock()
        barrier = threading.Barrier(self.client_amount)

        thread_pool = ThreadPool(self.client_amount, file_lock, barrier)
        
        thread_pool.start()
        
        while True:
            client_sock, ip = self.__accept_new_connection()
            thread_pool.assign_connection(client_sock, ip)

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
        self._server_socket.close()
        # Esperar a que terminen todos los hilos
        self.thread_pool.join()
        logging.info("action: shutdown | result: success")
