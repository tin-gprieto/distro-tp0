package common

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
)

const SUCCESS_ID = 1
const ERROR_ID = 2

type ServerAck struct {
	Id       uint32
	BetsRead uint32
}

func deserializeServerAck(data []byte) (*ServerAck, error) {
	if len(data) != 8 {
		return nil, fmt.Errorf("invalid data length")
	}
	ack := &ServerAck{}
	err := binary.Read(bytes.NewReader(data), binary.BigEndian, ack)
	if err != nil {
		return nil, fmt.Errorf("failed to deserialize server ack: %v", err)
	}
	return ack, nil
}

func rcvServerAck(conn net.Conn) (*ServerAck, error) {

	bytes, err := safe_recv(conn, 8)
	if err != nil {
		return nil, fmt.Errorf("failed to receive server ack: %v", err)
	}

	ack, err := deserializeServerAck(bytes)
	if err != nil {
		return nil, fmt.Errorf("failed to deserialize server ack: %v", err)
	}
	return ack, nil
}
