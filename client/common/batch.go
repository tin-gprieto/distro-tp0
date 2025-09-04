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
	BatchSize   uint32
	BatchBuffer *bytes.Buffer
}

func NewBatch() *Batch {
	return &Batch{
		BatchSize:   4,
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

func (b *Batch) Serialize() []byte {
	buf := new(bytes.Buffer)

	// Escribe en el buf la estructura en bytes
	length := uint32(len(b.BatchBuffer.Bytes()))
	binary.Write(buf, binary.BigEndian, length)
	buf.Write(b.BatchBuffer.Bytes())

	return buf.Bytes()
}

func (b *Batch) Send(conn net.Conn) (*Ack, error) {

	err := SafeSend(conn, b.Serialize())
	if err != nil {
		return nil, fmt.Errorf("failed to send batch: %v", err)
	}

	log.Debugf("action: batch_sent | result: success | size: %d", b.BatchSize)
	log.Debugf("action: waiting_for_ack | result: in_progress")

	rcv_ack, err := RcvAck(conn)

	return rcv_ack, err
}
