# Tabla de Contenidos - TP0 Sistemas Distribuidos

## [🔗 Tests del TP](https://github.com/7574-sistemas-distribuidos/tp0-tests)

- [Parte 1: Docker](#parte-1-docker)
  - [Ejercicio N°1](#ejercicio-n1)
  - [Ejercicio N°2](#ejercicio-n2)
  - [Ejercicio N°3](#ejercicio-n3)
  - [Ejercicio N°4](#ejercicio-n4)
- [Parte 2: Comunicaciones](#parte-2-comunicaciones)
  - [Ejercicio N°5](#ejercicio-n5)
  - [Ejercicio N°6](#ejercicio-n6)
  - [Ejercicio N°7](#ejercicio-n7)
- [Parte 3: Concurrencia](#parte-3-concurrencia)
  - [Ejercicio N°8](#ejercicio-n8)

# TP0 - Sistemas Distribuidos

## Parte 1: Docker

### Ejercicio N°1:

Para realizar lo pedido en el ejercicio 1, se realizó un script enteramente en bash que consta en escribir metiante cat y pipes sobre el archivo pasado por parámetro.

Primeramente lo referido a servidor y al nombre del docker-compose de manera estática:

        cat > $ARCHIVO <<EOF
        name: tp0
        services:
          server:
            container_name: server
            image: server:latest
            entrypoint: python3 /main.py
            environment:
              - PYTHONUNBUFFERED=1
              - LOGGING_LEVEL=DEBUG
            networks:
              - testing_net
        EOF
Por otro lado, lo referido a los cliente de forma dinámica (con la utilización de un for y el parámetro que indica la cantidad):

        for i in $(seq 1 $CANTIDAD); do
        cat >> $ARCHIVO <<EOF
        
          client$i:
            container_name: client$i
            image: client:latest
            entrypoint: /client
            environment:
              - CLI_ID=$i
              - CLI_LOG_LEVEL=DEBUG
            networks:
              - testing_net
            depends_on:
              - server
        EOF
        done

Y por último lo referido a la red que me monta y permite la conexión entre los servicios:

        cat >> $ARCHIVO <<EOF

        networks:
          testing_net:
            ipam:
              driver: default
              config:
                - subnet: 172.25.125.0/24
        EOF

### Ejercicio N°2:

Para lograr que se pueda modificar los archivos de configuración dentro de los clients y el server, lo que se debe hacer es persistirlos mediante un volume por fuera del contenedor. Por lo tanto, se requiere realizar dos cosas:

- Quitar las copias de los archivos dentro de los dockerfile del cliente
  
        FROM busybox:latest
        COPY --from=builder /build/bin/client /client
        
        ENTRYPOINT ["/bin/sh"]

- Agregar el config del server en el .dockerignore
- Agregar la instancia de los volumnes dentro del generar-compose.sh del ejercicio anterior

         server:
            ...
            volumes:
              - ./server/config.ini:/config.ini
  
          client$i:
            ...
            volumes:
              - ./client/config.yaml:/config.yaml

### Ejercicio N°3:

El objetivo del siguiente ejercicio es generar un nuevo sh para poder validar la funcionalidad del servidor mediante netcat pero con la condición de no instalarlo en el host.
Para cumplir con ese objetivo, se hizo uso de un contenedor temporal de docker para poder ejecutarlo y además se lo conecto a la docker network del contenedor para poder enviarle un mensaje.

En este caso, se optó por utilizar adicionalmente un script de python, principalmente para no harcodear ip y puertos supuestamente conocidos, sino utilizar el archivo de configuración del servidor para esto. El ejecutable de python en cuestión es el siguiente:

            config_file = "./server/config.ini"
            
            config = configparser.ConfigParser()
            config.read(config_file)

            service_name = config['DEFAULT']['SERVER_IP']
            port = config['DEFAULT']['SERVER_PORT']
            
            print(service_name, port)

Para luego utilizarse en el script de bash de la siguiente manera:

        output=$(python3 read_srv_config.py)
        SERVICE_NAME=$(echo $output | cut -d' ' -f1)
        PORT=$(echo $output | cut -d' ' -f2)
        
        RESPONSE=$(docker run --rm --network $NETWORK_NAME busybox sh -c \
            "echo '$MESSAGE' | nc $SERVICE_NAME $PORT")
        
        if [ "$RESPONSE" = "$MESSAGE" ]; then
            echo "action: test_echo_server | result: success"
            exit 0
        else
            echo "action: test_echo_server | result: failure"
            exit 1
        fi

Por lo tanto, para probar si el servidor echo funciona, el cliente debe recibir el mismo mensaje que envió.

### Ejercicio N°4:

Este ejercicio demanda poder tener una cierre grafeful de todos los contenedores cuando se corta su ejecuión con un SIGTERM, para esto deben cerrarse todos los file descriptors y sockets que hayan abierto.
Para poder manejar con tiempo estas operaciones, se decidió cambiar el -t del __docker compose -f stop__ a 10 para que se puedan realizar correctamente (docker compose -f docker-compose-dev.yaml stop -t 10).

Así mismo se implementaron las siguiente funciones de shutdown tanto para cliente como servidor:

    // CLIENT EN GO
    func ClientShutdown(client *Client) {
    	log.Infof("action: shutdown | result: in_progress | client_id: %s", client.config.ID)
    	client.Stop()
    	if client.conn != nil {
    		client.conn.Close()
    	}
    	log.Infof("action: shutdown | result: success | client_id: %s", client.config.ID)
    }

    // SERVER EN PYTHON
    def server_shutdown(self):
            logging.info("action: shutdown | result: in_progress")
            self._server_socket.close()
            logging.info("action: shutdown | result: success")

Y fueron inicializadas y llamadas dentro de:

- main() (main.go)

    	signals := make(chan os.Signal, 1)
    
    	signal.Notify(signals, syscall.SIGTERM)
    
    	go func() {
    		<-signals
    		common.ClientShutdown(client)
    	}()

- Server.__init__() (server.py)
 
        signal.signal(signal.SIGTERM, lambda signum, frame: (self.server_shutdown(), sys.exit(0)))

Adicionalmente para el cliente, se agregó una función para poder cortar con la iteración cuando llega la señal

	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {

		select {
		case <-c.interrupt:
			// Corta la ejecución del loop ante una señal de interrupción
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		default:
			// Continúa con la ejecución normal del loop
		}
      ...
  
## Parte 2: Comunicaciones
### Ejercicio N°5:
### Ejercicio N°6:
### Ejercicio N°7:
## Parte 3: Concurrencia
### Ejercicio N°8:
