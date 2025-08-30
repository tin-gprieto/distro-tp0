#!/bin/bash

NETWORK_NAME="tp0_testing_net"
MESSAGE="Hola Mundo"

# Leer SERVICE_NAME y PORT desde el archivo INI usando el script de Python
output=$(python3 read_srv_config.py)

# Asignar los valores de la salida a las variables SERVICE_NAME y PORT
SERVICE_NAME=$(echo $output | cut -d' ' -f1)
PORT=$(echo $output | cut -d' ' -f2)

# Contenedor temporal para enviar mensaje usando busybox
RESPONSE=$(docker run --rm --network $NETWORK_NAME busybox sh -c \
    "echo '$MESSAGE' | nc $SERVICE_NAME $PORT")

if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
    exit 0
else
    echo "action: test_echo_server | result: failure"
    exit 1
fi
