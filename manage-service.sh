#!/bin/bash

# Script para gestionar el servicio WiFi Analyzer

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start    - Iniciar el servicio"
    echo "  stop     - Detener el servicio"
    echo "  restart  - Reiniciar el servicio"
    echo "  status   - Mostrar el estado del servicio"
    echo "  logs     - Mostrar los logs del servicio"
    echo "  help     - Mostrar esta ayuda"
    echo ""
}

# Verificar si se proporcionó un comando
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Procesar el comando
case "$1" in
    start)
        echo "Iniciando el servicio WiFi Analyzer..."
        sudo systemctl start wifi-analyzer.service
        ;;
    stop)
        echo "Deteniendo el servicio WiFi Analyzer..."
        sudo systemctl stop wifi-analyzer.service
        ;;
    restart)
        echo "Reiniciando el servicio WiFi Analyzer..."
        sudo systemctl restart wifi-analyzer.service
        ;;
    status)
        echo "Estado del servicio WiFi Analyzer:"
        sudo systemctl status wifi-analyzer.service
        ;;
    logs)
        echo "Logs del servicio WiFi Analyzer:"
        sudo journalctl -u wifi-analyzer.service -f
        ;;
    help)
        show_help
        ;;
    *)
        echo "Comando desconocido: $1"
        show_help
        exit 1
        ;;
esac

exit 0
