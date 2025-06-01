#!/bin/bash

# Script de instalación para WiFi Analyzer en Raspberry Pi
# Este script configura el entorno y el servicio systemd

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir mensajes de estado
print_status() {
    echo -e "${GREEN}[+] $1${NC}"
}

# Función para imprimir advertencias
print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Función para imprimir errores
print_error() {
    echo -e "${RED}[-] $1${NC}"
}
export http_proxy=http://192.168.4.1:44088
export https_proxy=http://192.168.4.1:44088
source venv/bin/activate
curl -sSL https://get.docker.com | sh
#sudo docker run -d   --name mongodb   --network host   mongo:4.4.18
sudo docker run -d --name mongodb --network host --restart=always mongo:4.4.18

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar que se está ejecutando como root o con sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse con privilegios de superusuario (sudo)"
    exit 1
fi

# Obtener el directorio actual
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_DIR="$SCRIPT_DIR"

# Verificar que estamos en el directorio correcto
if [ ! -f "$APP_DIR/app.py" ]; then
    print_error "No se encontró app.py en el directorio actual. Asegúrate de ejecutar este script desde el directorio raíz de la aplicación."
    exit 1
fi

print_status "Iniciando la instalación de WiFi Analyzer..."

# Verificar requisitos previos
print_status "Verificando requisitos previos..."

# Verificar Python 3
if ! command_exists python3; then
    print_error "Python 3 no está instalado. Instalando..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
    if [ $? -ne 0 ]; then
        print_error "Error al instalar Python 3. Abortando."
        exit 1
    fi
fi

# Verificar MongoDB
if ! command_exists mongod; then
    print_warning "MongoDB no está instalado. Instalando..."
    
    # Añadir la clave GPG de MongoDB
#    apt-get install -y gnupg
#    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
    
    # Añadir el repositorio de MongoDB
#    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
    
    # Actualizar e instalar MongoDB
#    apt-get update
#    apt-get install -y mongodb-org
    
    # Iniciar y habilitar MongoDB
#    systemctl start mongod
#    systemctl enable mongod
    
    if [ $? -ne 0 ]; then
        print_warning "Error al instalar MongoDB. Intentando instalar la versión del repositorio de Debian..."
#        apt-get install -y mongodb
#        systemctl start mongodb
#        systemctl enable mongodb
        
        if [ $? -ne 0 ]; then
            print_error "Error al instalar MongoDB. Intentando configurar Docker..."
            
            # Verificar si Docker está instalado
            if ! command_exists docker; then
                print_warning "Docker no está instalado. Instalando..."
                curl -fsSL https://get.docker.com -o get-docker.sh
                sh get-docker.sh
                usermod -aG docker pi
                
                if [ $? -ne 0 ]; then
                    print_error "Error al instalar Docker. Abortando."
                    exit 1
                fi
            fi
            
            # Configurar MongoDB en Docker
            print_status "Configurando MongoDB en Docker..."
            docker run -d --name mongodb -p 27017:27017 --restart always mongo:4.4
            
            if [ $? -ne 0 ]; then
                print_error "Error al configurar MongoDB en Docker. Abortando."
                exit 1
            fi
        fi
    fi
fi

# Configurar entorno virtual
print_status "Configurando entorno virtual..."
if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv "$APP_DIR/venv"
    if [ $? -ne 0 ]; then
        print_error "Error al crear el entorno virtual. Abortando."
        exit 1
    fi
fi

# Instalar dependencias
print_status "Instalando dependencias..."
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    print_error "Error al instalar las dependencias. Abortando."
    #exit 1
fi

# Configurar el servicio systemd
print_status "Configurando el servicio systemd..."

# Obtener el usuario actual
CURRENT_USER=$(logname || echo "pi")
print_status "Configurando el servicio para el usuario: $CURRENT_USER"

# Crear el archivo de servicio
cat > /etc/systemd/system/wifi-analyzer.service << EOF
[Unit]
Description=WiFi Analyzer Service
After=network.target mongodb.service
Wants=mongodb.service

[Service]
User=$CURRENT_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
systemctl daemon-reload

# Habilitar el servicio
print_status "Habilitando el servicio para que se inicie automáticamente..."
systemctl enable wifi-analyzer.service

# Iniciar el servicio
print_status "Iniciando el servicio..."
systemctl start wifi-analyzer.service

# Verificar el estado del servicio
sleep 2
SERVICE_STATUS=$(systemctl is-active wifi-analyzer.service)
if [ "$SERVICE_STATUS" = "active" ]; then
    print_status "El servicio WiFi Analyzer se ha iniciado correctamente."
    
    # Obtener la dirección IP
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    
    print_status "La aplicación WiFi Analyzer está disponible en:"
    print_status "- URL local: http://localhost:8000"
    print_status "- URL en la red: http://$IP_ADDRESS:8000"
else
    print_error "El servicio WiFi Analyzer no se pudo iniciar. Verifica los logs con: sudo journalctl -u wifi-analyzer.service -e"
fi

# Hacer ejecutable el script de gestión
chmod +x "$APP_DIR/manage-service.sh"

print_status "Instalación completada."
print_status "Puedes gestionar el servicio con: $APP_DIR/manage-service.sh [start|stop|restart|status|logs]"
cd /home/pi/wifi-test/; source venv/bin/activate; python wifi_analyzer.py --use-mongodb --scan
ln -s /home/pi/wifi-test/wifi_analyzer.py /usr/bin/wifi_analizer
chmod 755 /usr/bin/wifi_analizer
exit 0
