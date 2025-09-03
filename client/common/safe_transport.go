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
