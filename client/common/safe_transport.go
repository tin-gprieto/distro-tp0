package common

import "net"

// Asegura que se envía todo el paquete - Short write handler
func safe_send(conn net.Conn, data []byte) error {
	packet_send_len := 0
	for packet_send_len < len(data) {
		n, err := conn.Write(data[packet_send_len:])
		if err != nil {
			return err
		}
		packet_send_len += n
	}
	return nil
}

// Asegura que se recibe todo el paquete - Short read handler
func safe_recv(conn net.Conn, length int) ([]byte, error) {
	buf := make([]byte, length)
	packet_recv_len := 0
	for packet_recv_len < length {
		n, err := conn.Read(buf[packet_recv_len:])
		if err != nil {
			return nil, err
		}
		packet_recv_len += n
	}
	return buf, nil
}
