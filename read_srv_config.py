import configparser
import sys

# Ruta del archivo de configuración (se pasa como argumento)
config_file = "./server/config.ini"

# Crear un parser de configuración
config = configparser.ConfigParser()
config.read(config_file)

# Leer los valores del archivo INI
service_name = config['DEFAULT']['SERVER_IP']
port = config['DEFAULT']['SERVER_PORT']

# Imprimir los valores para que el script de bash los lea
print(service_name, port)
