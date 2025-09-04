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
