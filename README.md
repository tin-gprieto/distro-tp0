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

Toda esta sección consta en la implementación de diferentes versiones de un protocolo de mensajería al cual llamaremos **MBP (Message Bet Protocol)**.

### Ejercicio N°5:

En este caso, el tipo de mensaje cambia y la respuesta del servidor tambíen, por lo tanto se implementa un protocolo para serializar/deserializar cada apuesta que se envía y tambien se incopora un acuse de recibo (ACK) para saber que la apuesta se recibió correctamente.

Las estructuras de cada mensaje son:

+----------------+----------------+----------------+----------------+----------------+----------------+
| length (4 B)   | first_name     | last_name      | document       | birthdate      | number (4 B)   |
|                | (string uint16)| (string uint16)| (string uint16)| (string uint16)|                |
+----------------+----------------+----------------+----------------+----------------+----------------+

con String uint16 como:

+----------------+----------------+
| length (2 B)   | payload (N B)  |
+----------------+----------------+

Y el ACK con id SUCCESS (0) o ERROR(1)

+----------------+
| id (4 B)       |
+----------------+

Así mismo se implementaron funciones __safe_send__ y __safe_rcv__ en python y __SafeSend__ y __SafeRcv__ en GO para evitar problemas de short write y short read. Basicamente todas funcionan de la misma manera, aseguran que cierta cantidad de bytes sean escritos/leídos. En el caso del envío se manda un cadena de bytes y se asegura que se mande todo el largo, y el caso de la recepción, se pasa por parámetro una longitud y se garantiza que se reciban.

Al envíar y recibir (se envía un paquete y se recibe un ACK) la lógica del echo server y del cliente no han cambiado considerablemente.

Cabe mencionar que se modificó el genera-compose.sh para incluir la información de la apuesta como variable de entrono del cliente.

### Ejercicio N°6:

En este ejercicio se siguen enviando apuestas pero de manera diferente. En este caso se leen de un archivo cierta cantidad, se cargan a un __batch__ y luego este se envía completamente al servidor para que registre todas las apuestas.

Para esto se implementó una estrcutura de batch para serializar/deserializar:

+----------------+----------------+
| length (4 B)   | payload (list[bet]) |
+----------------+----------------+

Y tambien un nuevo ACK para recibir que todo salió correctamente y se leyeron la cantidad de bets esperadas:

+----------------+----------------+
| id (4 B)       | bets_amount (4 B) |
+----------------+----------------+

Para cargar el batch, se abre al inicio el archivo, y se va leyendo de tramos para cargarlo completamente. Como este file descriptor se encuentra abierto a la hora de la ejecución del programa, tambien se incluye en el __ClientShutdown__.

La lófica de envió y recibo sigue siendo muy parecida a la original solo que con más información y más iteraciones.

### Ejercicio N°7:

Ahora se necesita un último paso, el servidor cuando tenga todas las apuestas de todos los clientes, necesita enviarle a cada uno la cantidad de ganadores de cada "agencia". Para esto, se modificaron algunas cosas del protocolo anterior de __batch__ y se creó un nuevo ACK (__WinnersAck__) para poder comunicar la respuesta de los ganadores.

En el caso de __batch__ se agregan dos campos_: 

- client_id: al cliente que está enviando los paquetes y por ende poder guardar su ip para luego comunicarle los ganadores
- is_last: indica al servidor si es el último paquete enviado así puede llevar la cuenta
 
+----------------+----------------+----------------+----------------+
| length (4 B)   | client_id (4 B)   | is_last (1 B)   | payload (list[bet]) |
+----------------+----------------+----------------+----------------+

Por el lado de __WinnersAck__, se reutiliza completamente la estructura de, el ahora llamado __BatchAck__. Si al momento de deserializar, se encuentra que tiene como id a WINNERS_ID (2), interpreta que en vez de ser la cantidad de apuestas almacenadas por el servidor en el envío del batch, es la cantidad de bytes de payload. Así, sabiendo el tamaño del payload, se puede leer la lista de documentos de ganadores.

+----------------+----------------+----------------+
| id (4 B)       | payload_size(4 B)| payload (list[document]) |
+----------------+----------------+----------------+

La lógica sí cambia un poco, ya que el cliente tiene que detectar cuál es su último paquete y el servidor tiene que manejar los avisos.

- En el caso del cliente, si el batch que envía es menor al maxAmount de bets que puede envía, tilda el isLast como verdadero.
- En el caso del servidor, si recibe un batch con isLast, registra al cliente en clientes preparados y luego chequea si debe realizar el sorteo. Si todos los clientes ya enviaron su último paquete, carga todas las apuestas y para cada conexión con cada cliente, envía el WinnersAck con su id correspondiente y la lista de documentos.
  

## Parte 3: Concurrencia
### Ejercicio N°8:
