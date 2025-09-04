# Ack
# Paquete de reconocimiento del servidor
# ID: 
#   - 0 - Success
#   - 1 - Error
# Bytes leídos: int 

from common.safe_transport import safe_send


SUCCESS_ID = 0
ERROR_ID = 1
WINNERS_ID = 2

class BatchAck:
    def __init__(self, id: int, bets_read: int):
        self.id = id
        self.bets_read = bets_read
    
    def serialize(self) -> bytes:
        return self.id.to_bytes(4, 'big') + self.bets_read.to_bytes(4, 'big')

    def send(self, client_sock) -> None:
        """Envía el paquete ACK al cliente."""
        data = self.serialize()
        safe_send(client_sock, data)

class WinnersAck:
    def __init__(self, winners: list[str]):
        self.id = WINNERS_ID
        self.winners = winners
        self.size = 4 + 2 + sum(2 + len(w) for w in winners)  # ID + count + each string length + each string

    def serialize(self) -> bytes:
        data = self.id.to_bytes(4, 'big') # ID uint32
        buf = bytes()
        for winner in self.winners:
            encoded_winner = winner.encode('utf-8') # String UTF-8
            buf += len(encoded_winner).to_bytes(2, 'big') # Length uint16
            buf +=  encoded_winner # String encoded

        data += len(buf).to_bytes(4, 'big') # Count uint32
        data += buf
        return data

    def send(self, client_sock) -> None:
        """Envía el paquete de ganadores al cliente."""
        data = self.serialize()
        safe_send(client_sock, data)
