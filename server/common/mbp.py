import logging
import struct

from common.utils import Bet
from common.safe_transport import safe_rcv, safe_send

# Ack
# Paquete de reconocimiento del servidor
# ID: 
#   - 0 - Success
#   - 1 - Error
# Bytes leídos: int 

SUCCESS_ID = 0
ERROR_ID = 1

class Ack:
    def __init__(self, id: int):
        self.id = id
    
    def serialize(self) -> bytes:
        return self.id.to_bytes(4, 'big')

    def send(self, client_sock) -> None:
        """Envía el paquete ACK al cliente."""
        data = self.serialize()
        safe_send(client_sock, data)

def __deserialize_string(data: bytes, offset: int):
    """Lee una string: primero 2 bytes de longitud, luego contenido."""
    length = struct.unpack_from(">H", data, offset)[0]
    offset += 2
    s = data[offset:offset+length].decode('utf-8')
    offset += length
    return s, offset

def __deserialize_bet(data: bytes) -> Bet:
    """Deserializa un Bet a partir de datos en bruto."""
    offset = 0

    # Agency
    agency = struct.unpack_from(">i", data, offset)[0]
    offset += 4

    first_name, offset = __deserialize_string(data, offset)
    last_name, offset = __deserialize_string(data, offset)
    document, offset = __deserialize_string(data, offset)
    birthdate_str, offset = __deserialize_string(data, offset)
    number = struct.unpack_from(">i", data, offset)[0]
    
    offset += 4

    bet = Bet(agency, first_name, last_name, document, birthdate_str, number)
    
    return bet

def recv_bet(client_sock):
    """Recibe un Bet serializado de forma simple."""
    try:
        # Leer longitud
        header = safe_rcv(client_sock, 4)
        total_length = struct.unpack(">I", header)[0]
        payload = safe_rcv(client_sock, total_length)
    except ConnectionError:
        raise ConnectionError("Conexión cerrada al leer longitud")

    bet = __deserialize_bet(payload)
    Ack(SUCCESS_ID).send(client_sock)        
    logging.info(f"action: ack_sent | result: success | ack_id: {SUCCESS_ID} ")
    return bet

