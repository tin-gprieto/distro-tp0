import struct
from common.safe_transport import safe_rcv

class Batch:
    def __init__(self, bytes: bytes, agency: int, isLast: bool):
        self.bytes = bytes
        self.size = len(self.bytes)
        self.agency = agency
        self.isLast = isLast

    def recv(client_sock):
        """Recibe un Bet serializado de forma simple."""
        # Leer longitud
        try:
            header = safe_rcv(client_sock, 9)
            total_length = struct.unpack(">I", header[0:4])[0]
            agency = struct.unpack_from(">i", header[4:8], 0)[0]
            is_last = struct.unpack(">B", header[8:9])[0]
            payload = safe_rcv(client_sock, total_length)
        except ConnectionError:
            raise ConnectionError("Conexión cerrada al leer longitud")

        return Batch(payload, agency, is_last)
