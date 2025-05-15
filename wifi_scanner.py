#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi Scanner para Raspberry Pi
Este script escanea redes WiFi en las bandas de 2.4GHz y 5GHz,
calcula distancias estimadas basadas en RSSI y genera gráficos.
"""

import subprocess
import re
import math
import json
import time
import os
from datetime import datetime

# Constantes para el cálculo de distancia
TX_POWER = -40  # dBm (potencia de transmisión típica a 1 metro)
PATH_LOSS_EXPONENT = 2.5  # Factor de propagación (2 en espacio libre, 2.7-4 en interiores)

def calculate_distance(rssi):
    """
    Calcula la distancia estimada basada en RSSI usando el modelo de pérdida de propagación logarítmica.

    Fórmula: d = 10^((TxPower - RSSI) / (10 * n))

    Donde:
    - d = distancia estimada en metros
    - TxPower = potencia de transmisión a 1 metro (dBm)
    - RSSI = intensidad de señal recibida (dBm)
    - n = factor de propagación

    Args:
        rssi (float): Intensidad de señal recibida en dBm

    Returns:
        float: Distancia estimada en metros
    """
    try:
        distance = 10 ** ((TX_POWER - rssi) / (10 * PATH_LOSS_EXPONENT))
        return round(distance, 2)
    except Exception as e:
        print(f"Error al calcular distancia: {e}")
        return None

def scan_wifi():
    """
    Escanea redes WiFi usando iwlist y devuelve los resultados procesados.

    Returns:
        list: Lista de diccionarios con información de cada red WiFi
    """
    try:
        # Verificar el estado de la interfaz antes del escaneo
        print("Verificando estado de la interfaz wlan0 antes del escaneo...")
        link_check = subprocess.run(["ip", "link", "show", "wlan0"],
                                  capture_output=True, text=True, check=True)
        print(f"Estado de la interfaz:\n{link_check.stdout}")

        # Intentar reiniciar la interfaz si está caída
        if "state DOWN" in link_check.stdout:
            print("La interfaz está caída, intentando reiniciarla...")
            subprocess.run(["sudo", "ip", "link", "set", "wlan0", "down"], check=True)
            time.sleep(1)
            subprocess.run(["sudo", "ip", "link", "set", "wlan0", "up"], check=True)
            time.sleep(3)

        # Ejecutar el comando de escaneo con timeout
        print("Ejecutando comando de escaneo...")
        try:
            result = subprocess.run(["sudo", "iwlist", "wlan0", "scan"],
                                  capture_output=True, text=True, check=True, timeout=15)

            # Verificar si hay algún mensaje de error en la salida
            if "Interface doesn't support scanning" in result.stdout:
                print(f"Error en la salida del escaneo: {result.stdout}")
                return []

            print("Escaneo completado con éxito.")

            # Procesar la salida
            scan_output = result.stdout
            networks = []

            # Patrones para extraer información
            cell_pattern = r'Cell \d+ - Address: ([0-9A-F:]+)'
            essid_pattern = r'ESSID:"([^"]*)"'
            channel_pattern = r'Channel:(\d+)'
            frequency_pattern = r'Frequency:([\d.]+) GHz'
            signal_pattern = r'Signal level=(-\d+) dBm'
            quality_pattern = r'Quality=(\d+)/(\d+)'
            encryption_pattern = r'Encryption key:(on|off)'

            # Dividir por celdas (cada red WiFi)
            cells = re.split(cell_pattern, scan_output)[1:]

            if not cells or len(cells) < 2:
                print(f"No se encontraron celdas en la salida del escaneo. Salida completa:\n{scan_output}")
                return []

            print(f"Se encontraron {len(cells)//2} redes WiFi.")

            # Procesar cada celda
            for i in range(0, len(cells), 2):
                if i+1 < len(cells):
                    mac = cells[i].strip()
                    info = cells[i+1]

                    # Extraer información
                    essid_match = re.search(essid_pattern, info)
                    channel_match = re.search(channel_pattern, info)
                    frequency_match = re.search(frequency_pattern, info)
                    signal_match = re.search(signal_pattern, info)
                    quality_match = re.search(quality_pattern, info)
                    encryption_match = re.search(encryption_pattern, info)

                    # Crear diccionario con la información
                    network = {
                        'mac': mac,
                        'essid': essid_match.group(1) if essid_match else 'Unknown',
                        'channel': int(channel_match.group(1)) if channel_match else None,
                        'frequency': float(frequency_match.group(1)) if frequency_match else None,
                        'signal': int(signal_match.group(1)) if signal_match else None,
                        'quality': int(quality_match.group(1)) / int(quality_match.group(2)) * 100 if quality_match else None,
                        'encrypted': encryption_match.group(1) == 'on' if encryption_match else None,
                    }

                    # Calcular distancia estimada
                    if network['signal']:
                        network['distance'] = calculate_distance(network['signal'])

                    networks.append(network)

            return networks

        except subprocess.TimeoutExpired:
            print("El comando de escaneo tardó demasiado tiempo. La interfaz podría estar ocupada.")
            return []

    except subprocess.CalledProcessError as e:
        print(f"Error al escanear redes WiFi: {e}")
        print(f"Salida de error: {e.stderr}")

        # Intentar obtener más información sobre el error
        try:
            print("Verificando estado de la interfaz después del error...")
            subprocess.run(["sudo", "iwconfig", "wlan0"], check=True)
            print("Verificando si hay procesos bloqueando la interfaz...")
            subprocess.run(["sudo", "lsof", "/dev/wlan0"], check=False)
        except:
            pass

        return []
    except Exception as e:
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return []

def save_scan_results(networks, filename=None):
    """
    Guarda los resultados del escaneo en un archivo JSON.

    Args:
        networks (list): Lista de redes WiFi
        filename (str, optional): Nombre del archivo. Si es None, se genera automáticamente.

    Returns:
        str: Ruta del archivo guardado
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wifi_scan_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(networks, f, indent=2)

    print(f"Resultados guardados en {filename}")
    return filename

def main():
    """Función principal"""
    print("Escaneando redes WiFi...")
    networks = scan_wifi()

    if networks:
        print(f"Se encontraron {len(networks)} redes WiFi:")

        # Ordenar por intensidad de señal
        networks.sort(key=lambda x: x.get('signal', -100), reverse=True)

        # Mostrar información
        for i, network in enumerate(networks):
            print(f"{i+1}. ESSID: {network['essid']}")
            print(f"   Canal: {network['channel']} ({network['frequency']} GHz)")
            print(f"   Señal: {network['signal']} dBm (Calidad: {network['quality']:.1f}%)")
            print(f"   Distancia estimada: {network['distance']} metros")
            print(f"   MAC: {network['mac']}")
            print()

        # Guardar resultados
        save_scan_results(networks)
    else:
        print("No se encontraron redes WiFi o hubo un error en el escaneo.")

if __name__ == "__main__":
    main()
