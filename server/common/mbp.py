import struct

from common.utils import Bet

def __read_string(data: bytes, offset: int):
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
    assert total_length == len(data) - 4, "Longitud no coincide"

    # Agency
    agency = struct.unpack_from(">i", data, offset)[0]
    offset += 4

    first_name, offset = __read_string(data, offset)
    last_name, offset = __read_string(data, offset)
    document, offset = __read_string(data, offset)
    birthdate_str, offset = __read_string(data, offset)
    number = struct.unpack_from(">i", data, offset)[0]
    
    offset += 4

    return Bet(agency, first_name, last_name, document, birthdate_str, number)

def recv_bet(client_sock):
    """Recibe un Bet serializado de forma simple."""
    # Leer longitud
    header = client_sock.recv(4)
    if not header:
        raise ConnectionError("Conexión cerrada al leer longitud")
    total_length = struct.unpack(">I", header)[0]

    # Leer payload completo
    payload = b''
    while len(payload) < total_length:
        chunk = client_sock.recv(total_length - len(payload))
        if not chunk:
            raise ConnectionError("Conexión cerrada al leer payload")
        payload += chunk

    return deserialize_bet(header + payload)
