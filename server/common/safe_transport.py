# Asegura que se recibe todo el payload - Short read handler
def safe_rcv(client_sock, total_length):
    """Recibe datos de forma segura, asegurando que se recibe todo el payload."""
    payload = b''
    while len(payload) < total_length:
        bytes_recv = client_sock.recv(total_length - len(payload))
        if not bytes_recv:
            raise ConnectionError("Conexión cerrada al leer payload")
        payload += bytes_recv
    return payload

# Asegura que se envía todo el paquete - Short write handler
def safe_send(client_sock, data):
    """Envía datos de forma segura, asegurando que se envía todo el paquete."""
    total_sent = 0
    while total_sent < len(data):
        bytes_sent = client_sock.send(data[total_sent:])
        if bytes_sent == 0:
            raise ConnectionError("Conexión cerrada al enviar payload")
        total_sent += bytes_sent