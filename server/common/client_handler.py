            

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
        self.connection = None
        self.has_connection = threading.Condition()
        self.file_lock = file_lock
        self.barrier = barrier

    def search_agency_winners(self, id):
        """Busca los ganadores de una agencia en las apuestas."""
        winners = []
        with self.file_lock:
            bets = load_bets()

        for bet in bets:
            if bet.agency == id and has_won(bet):
                winners.append(bet.document) 
        return winners
    
    def send_winners(self, client_socket, clientID):
        logging.info(f"action: sorteo | result: in_progress")
        winners = self.search_agency_winners(clientID)
        WinnersAck(winners).send(client_socket)
        logging.info(f"action: sorteo | result: success")
    
    def handle_agency(self, client_socket, ip):
        
        isLastPacket = False

        while not isLastPacket:
            bets, isLastPacket, clientID = rcv_bets_in_batch(client_socket)

            # Guardar batch de forma thread-safe
            with self.file_lock:
                store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                
        logging.info(f"action: ultima_apuesta_recibida | result: success | agencia_id: {clientID} | agency_ip: {ip}")
        # Último paquete, esperar a todos los clientes
        self.barrier.wait()
        self.send_winners(client_socket, clientID)
        client_socket.close()
                
    def assign_connection(self, client_socket, ip):
        with self.has_connection:
            self.connection = (client_socket, ip)
            self.has_connection.notify()

    def run(self):
        
        with self.has_connection:
            while not self.connection:
                self.has_connection.wait()  # esperar hasta que haya conexión
            client_socket, ip = self.connection

        self.handle_agency(client_socket, ip)
    