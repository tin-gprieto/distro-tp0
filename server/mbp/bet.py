import logging

from common.utils import Bet
from common.safe_transport import safe_rcv
from mbp.batch import Batch
from mbp.ack import SUCCESS_ID, BatchAck

def __deserialize_string(data: bytes, offset: int):
    """Lee una string: primero 2 bytes de longitud, luego contenido."""
    length = int.from_bytes(data[offset:offset+2], byteorder="big", signed=False)
    offset += 2
    s = data[offset:offset+length].decode('utf-8')
    offset += length
    return s, offset

def __deserialize_bet(data: bytes) -> Bet:
    """Deserializa un Bet a partir de datos en bruto."""
    offset = 0

    # Agency
    agency = int.from_bytes(data[offset:offset+4], byteorder="big", signed=True)
    offset += 4

    first_name, offset = __deserialize_string(data, offset)
    last_name, offset = __deserialize_string(data, offset)
    document, offset = __deserialize_string(data, offset)
    birthdate_str, offset = __deserialize_string(data, offset)
    number = int.from_bytes(data[offset:offset+4], byteorder="big", signed=True)
    
    offset += 4

    bet = Bet(agency, first_name, last_name, document, birthdate_str, number)
    
    return bet, offset

def __deserialize_bets_in_batch(batch: Batch) -> list[Bet]:
    """Deserializa un Batch a partir de datos en bruto."""
    bets = []
    offset = 0

    while offset < batch.size:
        bet, bet_size = __deserialize_bet(batch.bytes[offset:])
        bets.append(bet)
        offset += bet_size

    return bets

def rcv_bets_in_batch(client_sock) -> tuple[list[Bet], bool]:
    """Recibe un Batch de Bets desde el socket del cliente."""
    batch = Batch.recv(client_sock)
    bets = __deserialize_bets_in_batch(batch)
    BatchAck(SUCCESS_ID, len(bets)).send(client_sock)        
    logging.info(f"action: ack_sent | result: success | ack_id: {SUCCESS_ID} | bets_read: {len(bets)}")
    return bets, batch.isLast, batch.agency

def recv_bet(client_sock):
    """Recibe un Bet serializado de forma simple."""
    # Leer longitud
    try:
        header = safe_rcv(client_sock, 4)
        total_length = int.from_bytes(header, byteorder="big", signed=False)
        payload = safe_rcv(client_sock, total_length)
    except ConnectionError:
        raise ConnectionError("Conexión cerrada al leer longitud")
    BatchAck(SUCCESS_ID, 1).send(client_sock)        
    logging.info(f"action: ack_sent | result: success | ack_id: {SUCCESS_ID} | bets_read: 1")
    return __deserialize_bet(payload)


