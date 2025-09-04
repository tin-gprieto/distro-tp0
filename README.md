# TP0 - Sistemas Distribuidos

[Tests](<https://github.com/7574-sistemas-distribuidos/tp0-tests>)

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

## Parte 2: Comunicaciones

## Parte 3: Concurrencia
