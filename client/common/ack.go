package common

import (
	"encoding/binary"
	"fmt"
	"net"
)

const SUCCESS_ID = 0
const ERROR_ID = 1
const WINNERS_ID = 2

// Acknowledgment message structure

// SUCCESS_ID or ERROR_ID

// [4 bytes] ID
// [4 bytes] Bets stored amount (uint32)

// WINNERS_ID

// [4 bytes] ID
// [4 bytes] Payload size (bytes) (uint32)
// [2 bytes] Winner_1 length
// [N bytes] Winner_1
// [2 bytes] Winner_2 length
// [M bytes] Winner_2
// ...

type Ack struct {
	Id uint32
	//Cantidad de bets almacenadas (SUCCESS_ID - ERROR_ID)
	// Payload Size (WINNERS_ID)
	Size    uint32
	Winners []string
}

func NewAck(id uint32, size uint32, winners []string) *Ack {
	return &Ack{
		Id:      id,
		Size:    size,
		Winners: winners,
	}
}

func readWinners(data []byte, payloadSize uint32) ([]string, error) {
	winners := []string{}
	offset := 0
	end := int(payloadSize)
	for offset < end {
		if len(data[offset:]) < 2 {
			return nil, fmt.Errorf("not enough data for length")
		}
		length := binary.BigEndian.Uint16(data[offset : offset+2])
		offset += 2
		if len(data[offset:]) < int(length) {
			return nil, fmt.Errorf("not enough data for winner")
		}
		winner := string(data[offset : offset+int(length)])
		offset += int(length)
		winners = append(winners, winner)
	}

	return winners, nil
}

func RcvAck(conn net.Conn) (*Ack, error) {
	bytes, err := SafeRecv(conn, 8)
	ack_id := binary.BigEndian.Uint32(bytes[0:4])
	ack_size := binary.BigEndian.Uint32(bytes[4:8])
	if err != nil {
		return nil, fmt.Errorf("failed to receive server ack: %v", err)
	}

	if ack_id == WINNERS_ID {
		data, err := SafeRecv(conn, int(ack_size))
		if err != nil {
			return nil, fmt.Errorf("failed to receive winners data: %v", err)
		}
		winners, err := readWinners(data, ack_size)
		if err != nil {
			return nil, err
		}
		return NewAck(ack_id, ack_size, winners), nil
	}
	return NewAck(ack_id, ack_size, nil), nil
}
