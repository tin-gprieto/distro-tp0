import struct

from common.utils import Bet
from common.safe_transport import safe_rcv
from common.ack import SUCCESS_ID, ServerAck

def __deserialize_string(data: bytes, offset: int):
    """Lee una string: primero 2 bytes de longitud, luego contenido."""
    length = struct.unpack_from(">H", data, offset)[0]
    offset += 2
    s = data[offset:offset+length].decode('utf-8')
    offset += length
    return s, offset

def deserialize_bet(data: bytes) -> Bet:
    # Leer longitud total
    total_length = struct.unpack_from(">I", data, 0)[0]
    offset = 4

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
    
    return bet, offset

def recv_bet(client_sock):
    """Recibe un Bet serializado de forma simple."""
    # Leer longitud
    try:
        header = safe_rcv(client_sock, 4)
        total_length = struct.unpack(">I", header)[0]
        payload = safe_rcv(client_sock, total_length)
    except ConnectionError:
        raise ConnectionError("Conexión cerrada al leer longitud")

    ServerAck(SUCCESS_ID, 1).send(client_sock)

    return deserialize_bet(payload)
