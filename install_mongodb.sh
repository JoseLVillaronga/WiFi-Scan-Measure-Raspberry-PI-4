#!/bin/bash

# Script para instalar MongoDB en Raspberry Pi con Debian 12
# Este script instala MongoDB y configura el servicio

echo "=== Instalando MongoDB para WiFi Analyzer ==="

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script debe ejecutarse como root (sudo)."
  exit 1
fi

# Actualizar repositorios
echo "Actualizando repositorios..."
apt-get update

# Instalar dependencias
echo "Instalando dependencias..."
apt-get install -y gnupg curl

# Añadir clave GPG de MongoDB
echo "Añadiendo clave GPG de MongoDB..."
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
   gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor

# Añadir repositorio de MongoDB
echo "Añadiendo repositorio de MongoDB..."
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
   tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Actualizar repositorios
echo "Actualizando repositorios con MongoDB..."
apt-get update

# Instalar MongoDB
echo "Instalando MongoDB..."
apt-get install -y mongodb-org

# Crear directorio de datos si no existe
echo "Configurando directorio de datos..."
mkdir -p /data/db
chown -R mongodb:mongodb /data/db

# Configurar MongoDB para que se ejecute sin autenticación y solo en localhost
echo "Configurando MongoDB para ejecutarse sin autenticación y solo en localhost..."
cat > /etc/mongod.conf << EOF
# mongod.conf

# for documentation of all options, see:
#   http://docs.mongodb.org/manual/reference/configuration-options/

# Where and how to store data.
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

# network interfaces
net:
  port: 27017
  bindIp: 127.0.0.1

# how the process runs
processManagement:
  timeZoneInfo: /usr/share/zoneinfo
EOF

# Habilitar e iniciar el servicio
echo "Habilitando e iniciando el servicio MongoDB..."
systemctl daemon-reload
systemctl enable mongod
systemctl restart mongod

# Verificar estado del servicio
echo "Verificando estado del servicio MongoDB..."
systemctl status mongod

# Instalar pymongo
echo "Instalando pymongo para Python..."
pip3 install pymongo

echo "=== Instalación de MongoDB completada ==="
echo "Para verificar que MongoDB está funcionando, ejecute: mongo --eval 'db.runCommand({ connectionStatus: 1 })'"
echo "Para usar MongoDB con WiFi Analyzer, ejecute: python wifi_analyzer.py --use-mongodb"
