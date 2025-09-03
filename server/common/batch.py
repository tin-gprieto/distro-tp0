import logging
import struct
from common.utils import Bet, store_bets
from common.safe_transport import safe_rcv
from common.mbp import deserialize_bet
from common.ack import SUCCESS_ID, ServerAck

class Batch:
    def __init__(self, bets: list[Bet]):
        self.bets = bets

    def process(self) -> int:
        """Procesa un Batch a partir de datos en bruto."""
        store_bets(self.bets)
        return len(self.bets)

def deserialize_batch(data: bytes, batch_size: int) -> Batch:
    """Deserializa un Batch a partir de datos en bruto."""
    bets = []
    offset = 0

    logging.debug(f'action: deserialize_batch | result: in_progress | batch_size: {batch_size}')

    while offset < batch_size:
        bet, bet_size = deserialize_bet(data[offset:])
        
        logging.debug(f'action: deserialize_bet | result: success | bet_size: {bet_size}')
        
        bets.append(bet)
        offset += bet_size

    return Batch(bets)


def recv_batch(client_sock):
    """Recibe un Bet serializado de forma simple."""
    # Leer longitud
    try:
        header = safe_rcv(client_sock, 4)
        total_length = struct.unpack(">I", header)[0]
        payload = safe_rcv(client_sock, total_length)
    except ConnectionError:
        raise ConnectionError("Conexión cerrada al leer longitud")

    logging.debug(f'action: batch_received | result: success | batch_size: {total_length}')
    
    batch = deserialize_batch(payload, total_length)
    logging.debug(f'action: deserializing_batch | result: success | batch_size: {total_length}')
  
    ServerAck(SUCCESS_ID, len(batch.bets)).send(client_sock)
    logging.debug(f'action: ack_sent | result: success | ack_id: {SUCCESS_ID} | bets_read: {len(batch.bets)}')

    return batch