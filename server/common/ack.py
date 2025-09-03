from common.safe_transport import safe_send

# Ack
# Paquete de reconocimiento del servidor
# ID: 
#   - 0 - Success
#   - 1 - Error
# Bytes leídos: int 

SUCCESS_ID = 0
ERROR_ID = 1

class ServerAck:
    def __init__(self, id: int, bets_read: int):
        self.id = id
        self.bets_read = bets_read
    
    def serialize(self) -> bytes:
        return self.id.to_bytes(4, 'big') + self.bets_read.to_bytes(4, 'big')

    def send(self, client_sock) -> None:
        """Envía el paquete ACK al cliente."""
        data = self.serialize()
        safe_send(client_sock, data)