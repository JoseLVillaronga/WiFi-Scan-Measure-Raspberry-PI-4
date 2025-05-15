#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi Trends para Raspberry Pi
Este módulo genera visualizaciones de tendencias a lo largo del tiempo
basadas en datos almacenados en MongoDB.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import wifi_db

def generate_signal_strength_trend(db, network_name=None, mac=None, days=1, output_file=None):
    """
    Genera un gráfico de tendencia de intensidad de señal para una red específica.
    
    Args:
        db (WiFiDB): Instancia de WiFiDB
        network_name (str, optional): Nombre de la red (ESSID)
        mac (str, optional): Dirección MAC de la red
        days (int): Número de días a analizar
        output_file (str, optional): Ruta para guardar el gráfico
        
    Returns:
        str: Ruta del archivo guardado o None si hay un error
    """
    if not db.is_connected():
        print("No hay conexión a MongoDB.")
        return None
    
    if not network_name and not mac:
        print("Debe especificar al menos un nombre de red o dirección MAC.")
        return None
    
    # Definir período de tiempo
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Obtener historial de la red
    network_history = db.get_network_history(
        essid=network_name, 
        mac=mac, 
        start_time=start_time, 
        end_time=end_time
    )
    
    if not network_history:
        print(f"No se encontraron datos para la red {network_name or mac} en el período especificado.")
        return None
    
    # Convertir a DataFrame para facilitar el análisis
    data = []
    for entry in network_history:
        data.append({
            'timestamp': entry['timestamp'],
            'signal': entry['network']['signal'],
            'channel': entry['network']['channel'],
            'essid': entry['network']['essid']
        })
    
    df = pd.DataFrame(data)
    
    # Generar gráfico
    plt.figure(figsize=(12, 6))
    plt.title(f"Tendencia de Intensidad de Señal: {network_name or mac}", fontsize=16)
    plt.xlabel('Tiempo', fontsize=12)
    plt.ylabel('Intensidad de Señal (dBm)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Configurar ejes
    plt.ylim(-90, -20)
    
    # Formatear eje X para mostrar fechas/horas
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    
    # Dibujar línea de tendencia
    plt.plot(df['timestamp'], df['signal'], 'o-', color='blue', alpha=0.7, label='Intensidad de Señal')
    
    # Añadir línea de tendencia suavizada si hay suficientes puntos
    if len(df) > 5:
        try:
            from scipy.signal import savgol_filter
            window_size = min(15, len(df) - (len(df) % 2) - 1)  # Debe ser impar y menor que len(df)
            if window_size > 2:
                smoothed = savgol_filter(df['signal'], window_size, 3)
                plt.plot(df['timestamp'], smoothed, '-', color='red', alpha=0.8, label='Tendencia Suavizada')
        except ImportError:
            print("scipy no está instalado. No se generará la línea de tendencia suavizada.")
        except Exception as e:
            print(f"Error al generar línea de tendencia suavizada: {e}")
    
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Guardar o mostrar el gráfico
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico de tendencia guardado en {output_file}")
        return output_file
    else:
        plt.show()
        return None

def generate_channel_occupancy_trend(db, days=1, output_file=None):
    """
    Genera un gráfico de tendencia de ocupación de canales a lo largo del tiempo.
    
    Args:
        db (WiFiDB): Instancia de WiFiDB
        days (int): Número de días a analizar
        output_file (str, optional): Ruta para guardar el gráfico
        
    Returns:
        str: Ruta del archivo guardado o None si hay un error
    """
    if not db.is_connected():
        print("No hay conexión a MongoDB.")
        return None
    
    # Definir período de tiempo
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Obtener escaneos en el período
    scans = db.get_scans_in_timeframe(start_time, end_time)
    
    if not scans:
        print(f"No se encontraron datos en el período especificado.")
        return None
    
    # Preparar datos para el análisis
    timestamps = []
    channel_counts_2g = []
    channel_counts_5g = []
    
    for scan in scans:
        timestamp = scan['timestamp']
        networks = scan['networks']
        
        # Contar redes por canal
        channels_2g = {i: 0 for i in range(1, 15)}
        channels_5g = {}
        
        for network in networks:
            channel = network.get('channel')
            if channel:
                if channel <= 14:
                    channels_2g[channel] = channels_2g.get(channel, 0) + 1
                else:
                    channels_5g[channel] = channels_5g.get(channel, 0) + 1
        
        timestamps.append(timestamp)
        channel_counts_2g.append(channels_2g)
        channel_counts_5g.append(channels_5g)
    
    # Convertir a DataFrame para 2.4GHz
    df_2g = pd.DataFrame(channel_counts_2g, index=timestamps)
    
    # Generar gráfico para 2.4GHz
    plt.figure(figsize=(12, 8))
    plt.title(f"Tendencia de Ocupación de Canales 2.4GHz (Últimos {days} días)", fontsize=16)
    plt.xlabel('Tiempo', fontsize=12)
    plt.ylabel('Número de Redes', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Formatear eje X para mostrar fechas/horas
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    
    # Dibujar líneas para cada canal
    for channel in range(1, 15):
        if channel in df_2g.columns:
            plt.plot(df_2g.index, df_2g[channel], '-', label=f'Canal {channel}')
    
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Guardar o mostrar el gráfico
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico de ocupación de canales 2.4GHz guardado en {output_file}")
        return output_file
    else:
        plt.show()
    
    # Si hay datos de 5GHz, generar otro gráfico
    if any(bool(counts) for counts in channel_counts_5g):
        # Encontrar todos los canales 5GHz
        all_5g_channels = set()
        for counts in channel_counts_5g:
            all_5g_channels.update(counts.keys())
        
        # Convertir a DataFrame para 5GHz
        df_5g_data = []
        for counts in channel_counts_5g:
            row = {channel: counts.get(channel, 0) for channel in all_5g_channels}
            df_5g_data.append(row)
        
        df_5g = pd.DataFrame(df_5g_data, index=timestamps)
        
        # Generar gráfico para 5GHz
        plt.figure(figsize=(12, 8))
        plt.title(f"Tendencia de Ocupación de Canales 5GHz (Últimos {days} días)", fontsize=16)
        plt.xlabel('Tiempo', fontsize=12)
        plt.ylabel('Número de Redes', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Formatear eje X para mostrar fechas/horas
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Dibujar líneas para cada canal
        for channel in sorted(all_5g_channels):
            plt.plot(df_5g.index, df_5g[channel], '-', label=f'Canal {channel}')
        
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Guardar o mostrar el gráfico
        if output_file:
            output_file_5g = output_file.replace('.png', '_5GHz.png')
            plt.savefig(output_file_5g, dpi=300, bbox_inches='tight')
            print(f"Gráfico de ocupación de canales 5GHz guardado en {output_file_5g}")
        else:
            plt.show()
    
    return output_file

def generate_network_count_trend(db, days=1, output_file=None):
    """
    Genera un gráfico de tendencia del número de redes detectadas a lo largo del tiempo.
    
    Args:
        db (WiFiDB): Instancia de WiFiDB
        days (int): Número de días a analizar
        output_file (str, optional): Ruta para guardar el gráfico
        
    Returns:
        str: Ruta del archivo guardado o None si hay un error
    """
    if not db.is_connected():
        print("No hay conexión a MongoDB.")
        return None
    
    # Definir período de tiempo
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Obtener escaneos en el período
    scans = db.get_scans_in_timeframe(start_time, end_time)
    
    if not scans:
        print(f"No se encontraron datos en el período especificado.")
        return None
    
    # Preparar datos para el análisis
    timestamps = []
    total_counts = []
    counts_2g = []
    counts_5g = []
    
    for scan in scans:
        timestamp = scan['timestamp']
        networks = scan['networks']
        
        # Contar redes por banda
        count_2g = sum(1 for n in networks if n.get('channel') and n.get('channel') <= 14)
        count_5g = sum(1 for n in networks if n.get('channel') and n.get('channel') > 14)
        
        timestamps.append(timestamp)
        total_counts.append(len(networks))
        counts_2g.append(count_2g)
        counts_5g.append(count_5g)
    
    # Generar gráfico
    plt.figure(figsize=(12, 6))
    plt.title(f"Tendencia de Número de Redes WiFi (Últimos {days} días)", fontsize=16)
    plt.xlabel('Tiempo', fontsize=12)
    plt.ylabel('Número de Redes', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Formatear eje X para mostrar fechas/horas
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    
    # Dibujar líneas
    plt.plot(timestamps, total_counts, 'o-', color='blue', label='Total')
    plt.plot(timestamps, counts_2g, 'o-', color='green', label='2.4GHz')
    plt.plot(timestamps, counts_5g, 'o-', color='red', label='5GHz')
    
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Guardar o mostrar el gráfico
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico de tendencia de número de redes guardado en {output_file}")
        return output_file
    else:
        plt.show()
        return None

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generador de tendencias WiFi')
    
    parser.add_argument('--mongo-host', type=str, default='localhost', help='Host de MongoDB')
    parser.add_argument('--mongo-port', type=int, default=27017, help='Puerto de MongoDB')
    parser.add_argument('--mongo-db', type=str, default='wifi_analyzer', help='Nombre de la base de datos MongoDB')
    parser.add_argument('--days', type=int, default=1, help='Número de días a analizar')
    parser.add_argument('--network', type=str, help='Nombre de la red para análisis específico')
    parser.add_argument('--mac', type=str, help='Dirección MAC para análisis específico')
    parser.add_argument('--output-dir', type=str, help='Directorio para guardar los gráficos')
    
    args = parser.parse_args()
    
    # Conectar a MongoDB
    db = wifi_db.WiFiDB(host=args.mongo_host, port=args.mongo_port, db_name=args.mongo_db)
    
    if not db.is_connected():
        print("No se pudo conectar a MongoDB. Verifique que el servicio esté en ejecución.")
        return
    
    # Crear directorio de salida si no existe
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
    
    # Generar timestamp para los archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generar gráficos
    if args.network or args.mac:
        # Análisis específico de una red
        output_file = None
        if args.output_dir:
            network_name = args.network or args.mac
            output_file = os.path.join(args.output_dir, f"wifi_signal_trend_{network_name}_{timestamp}.png")
        
        generate_signal_strength_trend(db, args.network, args.mac, args.days, output_file)
    else:
        # Análisis general
        
        # Gráfico de ocupación de canales
        output_file = None
        if args.output_dir:
            output_file = os.path.join(args.output_dir, f"wifi_channel_trend_{timestamp}.png")
        
        generate_channel_occupancy_trend(db, args.days, output_file)
        
        # Gráfico de número de redes
        output_file = None
        if args.output_dir:
            output_file = os.path.join(args.output_dir, f"wifi_network_count_trend_{timestamp}.png")
        
        generate_network_count_trend(db, args.days, output_file)
    
    db.close()

if __name__ == "__main__":
    main()
