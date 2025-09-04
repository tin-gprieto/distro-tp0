import struct
from common.safe_transport import safe_rcv

class Batch:
    def __init__(self, bytes: bytes):
        self.bytes = bytes
        self.size = len(self.bytes)

    def recv(client_sock):
        """Recibe un Bet serializado de forma simple."""
        # Leer longitud
        try:
            header = safe_rcv(client_sock, 4)
            total_length = struct.unpack(">I", header)[0]
            payload = safe_rcv(client_sock, total_length)
        except ConnectionError:
            raise ConnectionError("Conexión cerrada al leer longitud")

        return Batch(payload)
