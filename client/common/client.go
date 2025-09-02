package common

import (
	"net"
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
	FirstName     string
	LastName      string
	Document      string
	BirthDate     string
	Number        string
}

// Client Entity that encapsulates how
type Client struct {
	config    ClientConfig
	conn      net.Conn
	interrupt chan struct{}
	bet       *Bet
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {

	bet, err := NewBet(
		config.ID,
		config.FirstName,
		config.LastName,
		config.Document,
		config.BirthDate,
		config.Number,
	)
	if err != nil {
		log.Criticalf("action: create_bet | result: fail | client_id: %v | error: %v",
			config.ID,
			err,
		)
		return nil
	}

	client := &Client{
		config:    config,
		interrupt: make(chan struct{}),
		bet:       bet,
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
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {

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

		err := sendBet(c.conn, c.bet)

		c.conn.Close()

		if err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | error: %v",
				err,
			)
			return
		}

		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
			c.bet.Document,
			c.bet.Number,
		)

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
