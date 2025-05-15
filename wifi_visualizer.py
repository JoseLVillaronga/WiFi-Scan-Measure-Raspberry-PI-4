#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi Visualizer para Raspberry Pi
Este script genera gráficos de redes WiFi basados en los datos escaneados.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
from datetime import datetime

# Constantes para los gráficos
CHANNEL_COLORS_2G = {
    1: '#3366CC',  # Azul
    2: '#3377CC',
    3: '#3388CC',
    4: '#3399CC',
    5: '#33AACC',
    6: '#33BBCC',  # Cian
    7: '#33CCBB',
    8: '#33CCAA',
    9: '#33CC99',
    10: '#33CC88',
    11: '#33CC77',
    12: '#33CC66',
    13: '#33CC55',  # Verde
    14: '#33CC44',
}

CHANNEL_COLORS_5G = {
    36: '#9933CC',  # Violeta
    40: '#9944CC',
    44: '#9955CC',
    48: '#9966CC',
    52: '#9977CC',
    56: '#9988CC',
    60: '#9999CC',
    64: '#99AACC',
    100: '#CC9933',  # Naranja
    104: '#CC9944',
    108: '#CC9955',
    112: '#CC9966',
    116: '#CC9977',
    120: '#CC9988',
    124: '#CC9999',
    128: '#CC99AA',
    132: '#CC99BB',
    136: '#CC99CC',
    140: '#CC99DD',
    144: '#CC99EE',
    149: '#CC3366',  # Rojo
    153: '#CC3377',
    157: '#CC3388',
    161: '#CC3399',
    165: '#CC33AA',
}

def load_scan_results(filename):
    """
    Carga los resultados de un escaneo desde un archivo JSON.
    
    Args:
        filename (str): Ruta del archivo JSON
        
    Returns:
        list: Lista de redes WiFi
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar el archivo {filename}: {e}")
        return []

def plot_channel_graph(networks, output_file=None):
    """
    Genera un gráfico de canales WiFi mostrando la intensidad de señal.
    
    Args:
        networks (list): Lista de redes WiFi
        output_file (str, optional): Ruta para guardar el gráfico. Si es None, se muestra en pantalla.
    """
    # Separar redes por banda
    networks_2g = [n for n in networks if n.get('channel') and n.get('channel') <= 14]
    networks_5g = [n for n in networks if n.get('channel') and n.get('channel') > 14]
    
    # Configurar el gráfico
    plt.figure(figsize=(12, 8))
    plt.title('Gráfico de Canal WiFi', fontsize=16)
    plt.xlabel('Canales WiFi', fontsize=12)
    plt.ylabel('Intensidad de Señal (dBm)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Configurar ejes
    plt.ylim(-90, -20)
    
    # Dibujar redes 2.4GHz
    if networks_2g:
        channels_2g = range(1, 15)
        plt.xticks(list(channels_2g))
        
        for network in networks_2g:
            channel = network.get('channel')
            signal = network.get('signal')
            essid = network.get('essid')
            
            if channel and signal:
                # Calcular ancho de banda (típicamente 20MHz = 4 canales)
                width = 4
                start_channel = max(1, channel - width//2)
                end_channel = min(14, channel + width//2)
                
                # Crear polígono para representar la señal
                x = np.linspace(start_channel, end_channel, 100)
                y_top = np.ones(100) * signal
                y_bottom = np.ones(100) * -90
                
                # Dibujar polígono
                color = CHANNEL_COLORS_2G.get(channel, '#AAAAAA')
                plt.fill_between(x, y_bottom, y_top, alpha=0.6, color=color)
                
                # Añadir etiqueta
                plt.text(channel, signal + 2, essid, fontsize=8, 
                         ha='center', va='bottom', color=color)
    
    # Guardar o mostrar el gráfico
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado en {output_file}")
    else:
        plt.tight_layout()
        plt.show()

def plot_network_list(networks, output_file=None):
    """
    Genera una visualización de lista de redes WiFi con sus detalles.
    
    Args:
        networks (list): Lista de redes WiFi
        output_file (str, optional): Ruta para guardar el gráfico. Si es None, se muestra en pantalla.
    """
    # Ordenar redes por intensidad de señal
    networks = sorted(networks, key=lambda x: x.get('signal', -100), reverse=True)
    
    # Configurar el gráfico
    fig, ax = plt.subplots(figsize=(10, len(networks) * 0.4 + 2))
    plt.title('Puntos de Acceso WiFi', fontsize=16)
    
    # Ocultar ejes
    ax.axis('off')
    
    # Crear tabla
    cell_text = []
    for network in networks:
        essid = network.get('essid', 'Unknown')
        channel = network.get('channel', 'N/A')
        signal = network.get('signal', 'N/A')
        distance = network.get('distance', 'N/A')
        frequency = network.get('frequency', 'N/A')
        mac = network.get('mac', 'N/A')
        
        # Determinar banda
        band = '2.4GHz' if channel and channel <= 14 else '5GHz'
        
        # Determinar color basado en la intensidad de señal
        if signal != 'N/A':
            if signal > -50:
                signal_color = 'green'
            elif signal > -70:
                signal_color = 'orange'
            else:
                signal_color = 'red'
        else:
            signal_color = 'black'
        
        # Añadir fila a la tabla
        cell_text.append([
            f"{essid} ({mac})",
            f"{signal} dBm",
            f"CH {channel} ({frequency} GHz)",
            f"{distance} m",
            band
        ])
    
    # Crear tabla
    table = ax.table(
        cellText=cell_text,
        colLabels=['SSID (MAC)', 'Señal', 'Canal (Frecuencia)', 'Distancia', 'Banda'],
        loc='center',
        cellLoc='left'
    )
    
    # Ajustar estilo de la tabla
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    
    # Colorear celdas según la intensidad de señal
    for i, network in enumerate(networks):
        signal = network.get('signal', 'N/A')
        if signal != 'N/A':
            if signal > -50:
                color = (0.8, 1, 0.8)  # Verde claro
            elif signal > -70:
                color = (1, 0.9, 0.7)  # Naranja claro
            else:
                color = (1, 0.8, 0.8)  # Rojo claro
            
            table[(i+1, 0)].set_facecolor(color)
    
    # Guardar o mostrar el gráfico
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Lista de redes guardada en {output_file}")
    else:
        plt.tight_layout()
        plt.show()

def main():
    """Función principal"""
    # Buscar el archivo JSON más reciente
    json_files = [f for f in os.listdir('.') if f.startswith('wifi_scan_') and f.endswith('.json')]
    
    if not json_files:
        print("No se encontraron archivos de escaneo. Ejecute wifi_scanner.py primero.")
        return
    
    # Ordenar por fecha (el más reciente primero)
    latest_file = sorted(json_files)[-1]
    print(f"Usando archivo de escaneo: {latest_file}")
    
    # Cargar datos
    networks = load_scan_results(latest_file)
    
    if not networks:
        print("No hay datos de redes WiFi para visualizar.")
        return
    
    # Generar gráficos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Gráfico de canales
    channel_graph_file = f"wifi_channel_graph_{timestamp}.png"
    plot_channel_graph(networks, channel_graph_file)
    
    # Lista de redes
    network_list_file = f"wifi_network_list_{timestamp}.png"
    plot_network_list(networks, network_list_file)
    
    print(f"Se generaron {len(networks)} visualizaciones de redes WiFi.")

if __name__ == "__main__":
    main()
