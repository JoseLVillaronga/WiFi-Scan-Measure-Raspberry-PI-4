#!/bin/bash

# Script para instalar MongoDB en Raspberry Pi con Debian 12
# Este script instala la versión de MongoDB disponible en los repositorios de Debian

echo "=== Instalando MongoDB para WiFi Analyzer en Raspberry Pi ==="

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script debe ejecutarse como root (sudo)."
  exit 1
fi

# Actualizar repositorios
echo "Actualizando repositorios..."
apt-get update

# Instalar MongoDB desde los repositorios de Debian
echo "Instalando MongoDB desde los repositorios de Debian..."
apt-get install -y mongodb

# Verificar si la instalación fue exitosa
if [ $? -ne 0 ]; then
  echo "Error: No se pudo instalar MongoDB. Intente con una instalación manual."
  exit 1
fi

# Detener el servicio para configurarlo
echo "Deteniendo el servicio MongoDB para configurarlo..."
systemctl stop mongodb

# Configurar MongoDB para que se ejecute sin autenticación y solo en localhost
echo "Configurando MongoDB para ejecutarse sin autenticación y solo en localhost..."
cat > /etc/mongodb.conf << EOF
# mongodb.conf

# Where to store the data.
dbpath=/var/lib/mongodb

# Where to log
logpath=/var/log/mongodb/mongodb.log
logappend=true

# Network settings
bind_ip = 127.0.0.1
port = 27017

# Enable journaling
journal=true
EOF

# Asegurarse de que los directorios existan y tengan los permisos correctos
echo "Configurando directorios y permisos..."
mkdir -p /var/lib/mongodb
mkdir -p /var/log/mongodb
chown -R mongodb:mongodb /var/lib/mongodb
chown -R mongodb:mongodb /var/log/mongodb

# Habilitar e iniciar el servicio
echo "Habilitando e iniciando el servicio MongoDB..."
systemctl daemon-reload
systemctl enable mongodb
systemctl start mongodb

# Verificar estado del servicio
echo "Verificando estado del servicio MongoDB..."
systemctl status mongodb

# Instalar pymongo en el entorno virtual
echo "Instalando pymongo en el entorno virtual..."
if [ -d "venv" ]; then
  # Activar el entorno virtual y instalar pymongo
  source venv/bin/activate
  pip install pymongo
  deactivate
  echo "pymongo instalado en el entorno virtual."
else
  echo "No se encontró el entorno virtual 'venv'. Por favor, instale pymongo manualmente con:"
  echo "source venv/bin/activate && pip install pymongo"
fi

echo "=== Instalación de MongoDB completada ==="
echo "Para verificar que MongoDB está funcionando, ejecute: mongosh --eval 'db.runCommand({ connectionStatus: 1 })'"
echo "Si mongosh no está disponible, pruebe con: mongo --eval 'db.runCommand({ connectionStatus: 1 })'"
echo "Para usar MongoDB con WiFi Analyzer, ejecute: python wifi_analyzer.py --use-mongodb"

# Mostrar información de conexión
echo ""
echo "Información de conexión a MongoDB:"
echo "- Host: localhost (127.0.0.1)"
echo "- Puerto: 27017"
echo "- Sin autenticación (no se requiere usuario/contraseña)"
echo "- Base de datos: wifi_analyzer (se creará automáticamente al usarla)"
