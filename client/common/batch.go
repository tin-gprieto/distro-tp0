package common

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
)

// Se define 8kB como la cantidad máxima de apuestas a enviar en un batch
const MaxBatchSize = 8192

type Batch struct {
	AgencyNum   uint32
	BatchSize   uint32
	BatchBuffer *bytes.Buffer
}

func NewBatch(agency string) *Batch {

	agency_num := uint32(0)
	fmt.Sscanf(agency, "%d", &agency_num)

	// 4 del size + 4 del agency + 1 del isLast
	header_size := uint32(4 + 4 + 1)

	return &Batch{
		AgencyNum:   agency_num,
		BatchSize:   header_size,
		BatchBuffer: new(bytes.Buffer),
	}
}

func (b *Batch) AddData(data []byte) bool {

	betSize := uint32(len(data))

	if b.BatchSize+betSize > MaxBatchSize {
		return false
	}

	b.BatchBuffer.Write(data)
	b.BatchSize += betSize

	return true
}

func (b *Batch) Serialize(bitLast uint8) []byte {
	buf := new(bytes.Buffer)

	// Escribe en el buf la estructura en bytes
	length := uint32(len(b.BatchBuffer.Bytes()))
	binary.Write(buf, binary.BigEndian, length)
	binary.Write(buf, binary.BigEndian, b.AgencyNum)
	binary.Write(buf, binary.BigEndian, bitLast)
	buf.Write(b.BatchBuffer.Bytes())

	return buf.Bytes()
}

func (b *Batch) Send(conn net.Conn, isLastOne bool) (*Ack, error) {

	bitLast := uint8(0)
	if isLastOne {
		bitLast = 1
	}

	err := SafeSend(conn, b.Serialize(bitLast))
	if err != nil {
		return nil, fmt.Errorf("failed to send batch: %v", err)
	}

	log.Debugf("action: batch_sent | result: success | size: %d", b.BatchSize)
	log.Debugf("action: waiting_for_ack | result: in_progress")

	rcv_ack, err := RcvAck(conn)

	return rcv_ack, err
}
