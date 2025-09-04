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
### Ejercicio N°4:
## Parte 2: Comunicaciones
### Ejercicio N°5:
### Ejercicio N°6:
### Ejercicio N°7:
## Parte 3: Concurrencia
### Ejercicio N°8:
