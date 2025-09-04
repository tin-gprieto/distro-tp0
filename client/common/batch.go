package common

import (
	"bytes"
	"encoding/binary"
	"encoding/csv"
	"fmt"
	"io"
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

func (b *Batch) addBet(bet *Bet) bool {

	betSerialized, err := bet.Serialize()
	if err != nil {
		return false
	}
	betSize := uint32(len(betSerialized))

	if b.BatchSize+betSize > MaxBatchSize {
		return false
	}

	b.BatchBuffer.Write(betSerialized)
	b.BatchSize += betSize

	return true
}

func (b *Batch) readAndLoad(agency string, maxAmount int, reader *csv.Reader) (bool, int, error) {

	linesLoaded := 0
	canLoadMore := true
	endOfFile := false

	for linesLoaded < maxAmount && canLoadMore {

		record, err := reader.Read()

		if err == io.EOF {
			endOfFile = true
			break
		}

		if err != nil {
			return endOfFile, linesLoaded, err
		}

		log.Debugf("action: read_line | result: success | line: %v", record)

		bet, err := NewBet(agency, record[0], record[1], record[2], record[3], record[4])
		if err != nil {
			return endOfFile, linesLoaded, err
		}

		canLoadMore = b.addBet(bet)
		linesLoaded++

	}

	log.Infof("action: batch_loaded | result: success | bets_amount: %d | size: %d", linesLoaded, b.BatchSize)

	return endOfFile, linesLoaded, nil
}

func (b *Batch) Serialize() ([]byte, error) {
	buf := new(bytes.Buffer)

	// Escribe en el buf la estructura en bytes
	length := uint32(len(b.BatchBuffer.Bytes()))
	binary.Write(buf, binary.BigEndian, length)
	buf.Write(b.BatchBuffer.Bytes())

	return buf.Bytes(), nil
}

func SendBatch(conn net.Conn, batch *Batch) (*Ack, error) {
	serializedBatch, err := batch.Serialize()
	if err != nil {
		return nil, fmt.Errorf("failed to serialize batch: %v", err)
	}

	err = safe_send(conn, serializedBatch)
	if err != nil {
		return nil, fmt.Errorf("failed to send batch: %v", err)
	}

	log.Debugf("action: batch_sent | result: success | size: %d", batch.BatchSize)
	log.Debugf("action: waiting_for_ack | result: in_progress")

	rcv_ack, err := RcvAck(conn)

	if err != nil {
		return nil, fmt.Errorf("failed to receive server ack: %v", err)
	}

	log.Debugf("action: ack_received | result: success | ack_id: %d | bets_read: %d", rcv_ack.Id, rcv_ack.BetsRead)

	return rcv_ack, nil
}
