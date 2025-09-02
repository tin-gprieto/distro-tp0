package common

import (
	"bytes"
	"encoding/binary"
	"fmt"
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
func (b *Bet) Serialize() ([]byte, error) {
	buf := new(bytes.Buffer)

	// Escribe en el buf la estructura en bytes
	binary.Write(buf, binary.BigEndian, b.Agency)
	writeString(buf, b.FirstName)
	writeString(buf, b.LastName)
	writeString(buf, b.Document)
	writeString(buf, b.Birthdate.Format("2006-01-02"))
	binary.Write(buf, binary.BigEndian, b.Number)

	// Longitud total
	data := buf.Bytes()
	final := new(bytes.Buffer)
	binary.Write(final, binary.BigEndian, uint32(len(data))) // longitud total
	final.Write(data)

	return final.Bytes(), nil
}

func sendBet(conn net.Conn, bet *Bet) error {
	data, err := bet.Serialize()
	if err != nil {
		return err
	}

	// net.Conn.Write ya envía todo el buffer (o error)
	_, err = conn.Write(data)
	if err != nil {
		return err
	}
	return nil
}
