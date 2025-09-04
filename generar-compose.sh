#!/bin/bash

# Verificar que se pasen dos parámetros
if [ $# -ne 2 ]; then
  echo "Uso: $0 <archivo_salida> <cantidad_clientes>"
  echo "Ejemplo: $0 docker-compose-dev.yaml 5"
  exit 1
fi

ARCHIVO=$1
CANTIDAD=$2

# Informar al usuario sobre los parámetros recibidos
echo "Nombre del archivo de salida: $ARCHIVO"
echo "Cantidad de clientes: $CANTIDAD"

# Definir el encabezado del archivo docker-compose.yml
# Crear o sobrescribir el archivo con el encabezado de nombre y servicios (server)
cat > $ARCHIVO <<EOF
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - CLIENT_AMOUNT=$CANTIDAD
    volumes:
      - ./server/config.ini:/config.ini
    networks:
      - testing_net
EOF

# Bucle para generar cada cliente
for i in $(seq 1 $CANTIDAD); do
cat >> $ARCHIVO <<EOF

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
    volumes:
      - ./client/config.yaml:/config.yaml
      - ./.data/agency-$i.csv:/agency.csv
    networks:
      - testing_net
    depends_on:
      - server
EOF
done

# Definir la red entre servidor y clientes
cat >> $ARCHIVO <<EOF

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF

echo "Archivo $ARCHIVO generado correctamente."
