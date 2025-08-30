#!/bin/bash

# Constantes
readonly TEST_MESSAGE="Prueba echo server"
readonly COMPOSE_FILE="docker-compose-test.yaml"

# Crear un docker-compose temporal que incluya el test
cat > "$COMPOSE_FILE" << EOF
name: tp0-test
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

  test-echo:
    container_name: test-echo
    image: alpine:latest
    entrypoint: /bin/sh
    command: -c "apk add --no-cache netcat-openbsd && sleep 5 && echo 'Prueba echo server' | timeout 10 nc -w 5 server 12345"
    networks:
      - testing_net
    depends_on:
      - server


networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF

# Iniciar solo el servidor primero
echo "Iniciando servidor..."
docker compose -f "$COMPOSE_FILE" up -d server

# Esperar a que el servidor esté listo
echo "Esperando a que el servidor esté listo..."
sleep 8

# Ejecutar el test y capturar el resultado
echo "Ejecutando test de echo server..."
echo "Mensaje de prueba: '$TEST_MESSAGE'"
TEST_RESULT=$(docker compose -f "$COMPOSE_FILE" run --rm test-echo 2>&1)

# Limpiar recursos
docker compose -f "$COMPOSE_FILE" down 2>/dev/null
rm -f "$COMPOSE_FILE" 2>/dev/null

# Extraer solo la respuesta del echo (última línea)
ACTUAL_RESPONSE=$(echo "$TEST_RESULT" | tail -n 1 | tr -d '\r')

# Verificar el resultado
if [ "$ACTUAL_RESPONSE" = "$TEST_MESSAGE" ]; then
    echo "Mensaje recibido: $ACTUAL_RESPONSE"
    echo "action: test_echo_server | result: success"
    exit 0
else
    echo "Mensaje recibido: '$ACTUAL_RESPONSE'"
    echo "action: test_echo_server | result: fail"
    exit 1
fi

