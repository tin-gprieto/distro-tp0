            

import logging
import threading

from common.utils import has_won, load_bets, store_bets
from mbp.ack import WinnersAck
from mbp.bet import rcv_bets_in_batch


class ClientHandlerThread(threading.Thread):
    """
    Hilo fijo que maneja conexiones asignadas según addr.
    """
    def __init__(self, socket, file_lock, barrier):
        super().__init__()
        self.socket = socket
        self.file_lock = file_lock
        self.sorteo_barrier = barrier

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
    
    def handle_agency(self):
        
        isLastPacket = False

        while not isLastPacket:
            bets, isLastPacket, clientID = rcv_bets_in_batch(self.socket)

            # Guardar batch de forma thread-safe
            with self.file_lock:
                store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                
        logging.info(f"action: ultima_apuesta_recibida | result: success | agencia_id: {clientID}")
        # Último paquete, esperar a todos los clientes
        self.sorteo_barrier.wait()
        self.send_winners(self.socket, clientID)
        self.socket.close()


    def run(self):
        logging.debug(f"Thread handler starting with connection.")
        self.handle_agency()
    