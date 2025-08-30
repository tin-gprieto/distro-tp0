#!/bin/bash

CONFIG_FILE="./server/config.ini"
NETWORK_NAME="tp0_testing_net"
MESSAGE="Hola Mundo"

# Leer SERVICE_NAME y PORT desde el archivo INI usando Python
read SERVICE_NAME PORT < <(
python3 - <<EOF
import configparser
config = configparser.ConfigParser()
config.read('$CONFIG_FILE')
print(config['DEFAULT']['SERVER_IP'], config['DEFAULT']['SERVER_PORT'])
EOF
)

# Contenedor temporal para enviar mensaje usando busybox
RESPONSE=$(docker run --rm --network $NETWORK_NAME busybox sh -c \
    "echo '$MESSAGE' | nc $SERVICE_NAME $PORT")

if [ "$RESPONSE" == "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
    exit 0
else
    echo "action: test_echo_server | result: failure"
    exit 1
fi
