package common

import (
	"encoding/csv"
	"net"
	"os"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	MaxAmount     int
}

// Client Entity that encapsulates how
type Client struct {
	config    ClientConfig
	conn      net.Conn
	interrupt chan struct{}
	file      *os.File
	reader    *csv.Reader
}

func SetFile() *os.File {
	path := "./agency.csv"
	file, err := os.Open(path)
	if err != nil {
		return nil
	}
	return file
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {

	file := SetFile()

	if file == nil {
		log.Errorf("action: set_file | result: fail")
		return nil
	}

	client := &Client{
		config:    config,
		interrupt: make(chan struct{}),
		file:      file,
		reader:    csv.NewReader(file),
	}
	return client
}

func (c *Client) Stop() {
	close(c.interrupt)
}

func ClientShutdown(client *Client) {
	log.Infof("action: shutdown | result: in_progress | client_id: %s", client.config.ID)
	client.Stop()
	if client.conn != nil {
		client.conn.Close()
	}
	if client.file != nil {
		client.file.Close()
	}
	log.Infof("action: shutdown | result: success | client_id: %s", client.config.ID)
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {

	eof := false

	for !eof {

		select {
		case <-c.interrupt:
			// Corta la ejecución del loop ante una señal de interrupción
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		default:
			// Continúa con la ejecución normal del loop
		}

		// Create the connection the server in every loop iteration. Send an
		c.createClientSocket()

		batch := NewBatch()

		finished, betsLoaded, err := batch.readAndLoad(c.config.ID, c.config.MaxAmount, c.reader)

		if err != nil {

			log.Errorf("action: batch_loaded | result: fail | error: %v", err)

		} else {

			ack, err := SendBatch(c.conn, batch)

			if err != nil {
				log.Errorf("action: apuesta_enviada | result: fail | error: %v", err)
				break
			}

			if ack.Id != SUCCESS_ID && ack.BetsRead != uint32(betsLoaded) {
				log.Errorf("action: apuesta_enviada | result: fail | error: %v", err)
			}
		}

		c.conn.Close()

		log.Infof("action: apuesta_enviada | result: success | cantidad: %v", betsLoaded)

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)

		eof = finished

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
