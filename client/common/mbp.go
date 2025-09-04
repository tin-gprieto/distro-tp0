package common

import (
	"bytes"
	"encoding/binary"
	"encoding/csv"
	"fmt"
	"io"
	"net"
	"strconv"
	"time"
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

type Bet struct {
	Agency    uint32
	FirstName string
	LastName  string
	Document  string
	Birthdate time.Time
	Number    uint32
}

func NewBet(agency string, firstName string, lastName string, document string, birthdate string, number string) (*Bet, error) {
	parsedDate, err := time.Parse("2006-01-02", birthdate)
	if err != nil {
		return nil, fmt.Errorf("invalid birthdate format: %v", err)
	}

	intAgency, err := strconv.ParseUint(agency, 10, 32)
	if err != nil {
		return nil, fmt.Errorf("invalid agency format: %v", err)
	}

	intNumber, err := strconv.ParseUint(number, 10, 32)
	if err != nil {
		return nil, fmt.Errorf("invalid number format: %v", err)
	}

	return &Bet{
		Agency:    uint32(intAgency),
		FirstName: firstName,
		LastName:  lastName,
		Document:  document,
		Birthdate: parsedDate,
		Number:    uint32(intNumber),
	}, nil
}

// writeString serializa una string con longitud (uint16) antes de los bytes
func writeString(buf *bytes.Buffer, s string) {
	binary.Write(buf, binary.BigEndian, uint16(len(s)))
	buf.Write([]byte(s))
}

// Serialize convierte Bet en []byte
func (b *Bet) Serialize() []byte {
	buf := new(bytes.Buffer)

	// Escribe en el buf la estructura en bytes
	binary.Write(buf, binary.BigEndian, b.Agency)
	writeString(buf, b.FirstName)
	writeString(buf, b.LastName)
	writeString(buf, b.Document)
	writeString(buf, b.Birthdate.Format("2006-01-02"))
	binary.Write(buf, binary.BigEndian, b.Number)

	return buf.Bytes()
}

func (b *Bet) Send(conn net.Conn) (*Ack, error) {

	err := SafeSend(conn, b.Serialize())

	if err != nil {
		return nil, fmt.Errorf("failed to send batch: %v", err)
	}

	log.Debugf("action: bet_sent | result: success")
	log.Debugf("action: waiting_for_ack | result: in_progress")

	rcv_ack, err := RcvAck(conn)

	return rcv_ack, err
}

func ReadBet(agency string, reader *csv.Reader) (*Bet, error) {
	record, err := reader.Read()

	if err == io.EOF {
		return nil, io.EOF
	}

	if err != nil {
		return nil, err
	}

	log.Debugf("action: read_line | result: success | line: %v", record)

	return NewBet(agency, record[0], record[1], record[2], record[3], record[4])

}
