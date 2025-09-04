import logging
import socket

from common.utils import has_won, load_bets
from common.mbp import WinnersAck

WAITLIST_SIZE = 5

class AgencyHandler:
    def __init__(self):
        # Diccionario (id, ip)
        self.__agencies_waitlist = {}
        # Diccionario (ip, socket)
        self.__agencies_ready = {}

    def is_in_the_waitlist(self, ip):
        """Verifica si una agencia está en la lista de espera."""
        return ip in self.__agencies_waitlist.values()

    def add_to_waitlist(self, ip, id):
        """Registra la dirección de una agencia con su ID."""
        self.__agencies_waitlist[id] = ip


    def __send_winners_to_agency(self, socket: socket.socket, winners: list[str]):
        """Envía datos a la dirección de la agencia."""
        if socket is None:
            raise ValueError(f"Agencia no registrada.")

        WinnersAck(winners).send(socket)
        socket.close()
        
    def __search_agency_winners(self, id):
        """Busca los ganadores de una agencia en las apuestas."""
        winners = []
        bets = 0
        for bet in load_bets():
            if bet.agency == id and has_won(bet):
                winners.append(bet.document)
            bets += 1   
        return winners

    def register_socket(self, ip, socket):
        """Registra el socket de una agencia."""
        self.__agencies_ready[ip] = socket

    def all_agencies_are_ready(self):
        """Verifica si todas las agencias están listas."""
        notify_all = len(self.__agencies_ready) == WAITLIST_SIZE
        return notify_all

    def notify_winners_to_agencies(self):
        """Notifica a las agencias sobre los ganadores."""
        for client_id, ip in self.__agencies_waitlist.items():
            winners = self.__search_agency_winners(client_id)
            self.__send_winners_to_agency(self.__agencies_ready[ip], winners)
            logging.info(f"action: notificar_ganadores | result: success | agency_id: {client_id} | cantidad: {len(winners)}")
