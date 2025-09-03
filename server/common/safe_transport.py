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