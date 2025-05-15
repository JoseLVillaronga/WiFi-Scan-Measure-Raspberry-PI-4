#!/bin/bash

# Script de instalación para WiFi Analyzer
# Este script configura el entorno necesario para ejecutar el analizador WiFi

echo "=== Configurando WiFi Analyzer para Raspberry Pi ==="

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script debe ejecutarse como root (sudo)."
  exit 1
fi

# Actualizar repositorios
echo "Actualizando repositorios..."
apt-get update

# Instalar dependencias del sistema
echo "Instalando dependencias del sistema..."
apt-get install -y python3-venv python3-pip python3-dev libatlas-base-dev

# Verificar si el directorio ya existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual Python..."
    python3 -m venv venv
else
    echo "El entorno virtual ya existe."
fi

# Activar entorno virtual y instalar dependencias Python
echo "Instalando dependencias Python..."
source venv/bin/activate
pip install --upgrade pip
pip install scapy matplotlib numpy pandas

# Hacer ejecutables los scripts
echo "Configurando permisos de ejecución..."
chmod +x wifi_scanner.py wifi_visualizer.py wifi_analyzer.py

# Verificar adaptadores WiFi
echo "Verificando adaptadores WiFi..."
iw dev

# Desbloquear WiFi si está bloqueado
echo "Desbloqueando WiFi..."
rfkill unblock wifi

# Activar interfaz WiFi
echo "Activando interfaz WiFi..."
ip link set wlan0 up

echo "=== Instalación completada ==="
echo "Para activar el entorno virtual, ejecute: source venv/bin/activate"
echo "Para realizar un escaneo, ejecute: python wifi_analyzer.py --scan"
echo "Para realizar escaneos continuos, ejecute: python wifi_analyzer.py --continuous --interval 60"
