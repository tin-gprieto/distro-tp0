import signal
import socket
import logging
import sys

from common.mbp import rcv_bets_in_batch
from common.utils import store_bets
from common.agency_handler import AgencyHandler

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self.agency_handler = AgencyHandler()
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        signal.signal(signal.SIGTERM, lambda signum, frame: (self.server_shutdown(), sys.exit(0)))
        
        while True:
            client_sock, addr = self.__accept_new_connection()
            self.__handle_client_connection(client_sock, addr[0])

    def __handle_client_connection(self, client_sock, ip):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
    
            if not self.agency_handler.is_in_the_waitlist(ip):
                
                bets, isLastOne, clientID = rcv_bets_in_batch(client_sock)

                store_bets(bets)
                
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            
                if isLastOne:
                    self.agency_handler.add_to_waitlist(ip, clientID)
                    logging.info(f"action: ultima_apuesta_recibida | result: success | agencia_id: {clientID} | agency_ip: {ip}")

                client_sock.close()
                
            else:
                
                self.agency_handler.register_socket(ip, client_sock)
                logging.info(f"action: agencia_lista | result: success | agency_ip: {ip}")
                
                if self.agency_handler.all_agencies_are_ready():
                    logging.info(f"action: sorteo | result: in_progress")
                    self.agency_handler.notify_winners_to_agencies()
                    logging.info(f"action: sorteo | result: success")

        except OSError as e:
            logging.error(f"action: apuesta_recibida | result: fail | error: {e}")
            

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
        return c, addr
    
    def server_shutdown(self):
        logging.info("action: shutdown | result: in_progress")
        self._server_socket.close()
        logging.info("action: shutdown | result: success")
