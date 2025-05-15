#!/bin/bash

# Script para instalar MongoDB en Raspberry Pi con Docker
# Este script instala Docker si no está instalado, y luego ejecuta MongoDB en un contenedor

echo "=== Instalando MongoDB para WiFi Analyzer usando Docker ==="

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script debe ejecutarse como root (sudo)."
  exit 1
fi

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
  echo "Docker no está instalado. Instalando Docker..."
  apt-get update
  apt-get install -y docker.io
  systemctl enable --now docker
  usermod -aG docker $SUDO_USER
  echo "Docker instalado correctamente."
else
  echo "Docker ya está instalado."
fi

# Verificar si el contenedor de MongoDB ya existe
if docker ps -a --filter "name=mongodb" --format '{{.Names}}' | grep -q "mongodb"; then
  echo "El contenedor 'mongodb' ya existe."
  
  # Verificar si el contenedor está en ejecución
  if docker ps --filter "name=mongodb" --format '{{.Names}}' | grep -q "mongodb"; then
    echo "El contenedor 'mongodb' ya está en ejecución."
  else
    echo "Iniciando el contenedor 'mongodb'..."
    docker start mongodb
  fi
else
  # Ejecutar MongoDB en Docker
  echo "Ejecutando MongoDB en Docker..."
  docker run -d \
    --name mongodb \
    --network host \
    --restart always \
    mongo:4.4.18
  
  if [ $? -eq 0 ]; then
    echo "MongoDB iniciado correctamente en Docker."
  else
    echo "Error al iniciar MongoDB en Docker."
    exit 1
  fi
fi

# Verificar si mongosh está instalado
if ! command -v mongosh &> /dev/null; then
  echo "Instalando MongoDB Shell (mongosh)..."
  apt-get update
  apt-get install -y mongodb-mongosh
  
  if [ $? -ne 0 ]; then
    echo "No se pudo instalar mongosh desde los repositorios. Intentando con el paquete mongodb-shell..."
    apt-get install -y mongodb-shell
    
    if [ $? -ne 0 ]; then
      echo "No se pudo instalar mongosh. Puedes conectarte a MongoDB usando el cliente mongo dentro del contenedor:"
      echo "docker exec -it mongodb mongo"
    fi
  fi
else
  echo "MongoDB Shell (mongosh) ya está instalado."
fi

# Instalar pymongo en el entorno virtual si existe
if [ -d "venv" ]; then
  echo "Instalando pymongo en el entorno virtual..."
  if [ -n "$SUDO_USER" ]; then
    su - $SUDO_USER -c "cd $(pwd) && source venv/bin/activate && pip install pymongo && deactivate"
  else
    source venv/bin/activate && pip install pymongo && deactivate
  fi
  echo "pymongo instalado en el entorno virtual."
else
  echo "No se encontró el entorno virtual 'venv'. Asegúrate de instalar pymongo manualmente:"
  echo "source venv/bin/activate && pip install pymongo"
fi

# Configurar MongoDB para que se inicie automáticamente
echo "Configurando MongoDB para que se inicie automáticamente..."
docker update --restart=always mongodb

echo "=== Instalación de MongoDB completada ==="
echo "MongoDB está ejecutándose en localhost:27017 sin autenticación."
echo "Para verificar que MongoDB está funcionando, ejecute: mongosh"
echo "Para usar MongoDB con WiFi Analyzer, ejecute: python wifi_analyzer.py --use-mongodb"

# Mostrar información de conexión
echo ""
echo "Información de conexión a MongoDB:"
echo "- Host: localhost (127.0.0.1)"
echo "- Puerto: 27017"
echo "- Sin autenticación (no se requiere usuario/contraseña)"
echo "- Base de datos: wifi_analyzer (se creará automáticamente al usarla)"
