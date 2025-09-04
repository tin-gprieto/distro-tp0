            

import logging
import threading

from common.utils import has_won, load_bets, store_bets
from mbp.ack import WinnersAck
from mbp.bet import rcv_bets_in_batch


class ClientHandlerThread(threading.Thread):
    """
    Hilo fijo que maneja conexiones asignadas según addr.
    """
    def __init__(self, thread_id, file_lock, barrier):
        super().__init__()
        self.thread_id = thread_id
        self.connections = []
        self.file_lock = file_lock
        self.barrier = barrier
        self.cv = threading.Condition()

    def search_agency_winners(self, id):
        """Busca los ganadores de una agencia en las apuestas."""
        winners = []
        with self.file_lock:
            for bet in load_bets():
                if bet.agency == id and has_won(bet):
                    winners.append(bet.document) 
        return winners
    
    def send_winners(self, client_socket, clientID):
        logging.info(f"action: sorteo | result: in_progress")
        winners = self.search_agency_winners(clientID)
        WinnersAck(winners).send(client_socket)
        logging.info(f"action: sorteo | result: success")
    
    def handle_agency(self, client_socket, ip):
        try:
            bets, isLastOne, clientID = rcv_bets_in_batch(client_socket)

            # Guardar batch de forma thread-safe
            with self.file_lock:
                store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')

            if isLastOne:
                logging.info(f"action: ultima_apuesta_recibida | result: success | agencia_id: {clientID} | agency_ip: {ip}")
                # Último paquete, esperar a todos los clientes
                self.barrier.wait()
                self.send_winners(client_socket, clientID)
                client_socket.close()
        except OSError as e:
            logging.error(f"action: apuesta_recibida | result: fail | error: {e}")
            if client_socket:
                client_socket.close()
                
    def assign_connection(self, client_socket, ip):
        with self.cv:
            self.connections.append((client_socket, ip))
            self.cv.notify()

    def run(self):
        while True:
            with self.cv:
                while not self.connections:
                    self.cv.wait()  # esperar hasta que haya conexión
                client_socket, ip = self.connections.pop(0)

            self.handle_agency(client_socket, ip)
    