#!/home/pi/wifi-test/venv/bin/python
# -*- coding: utf-8 -*-

"""
WiFi Analyzer para Raspberry Pi
Este script integra el escáner y el visualizador de redes WiFi.
"""

import argparse
import os
import time
import subprocess
from datetime import datetime, timedelta
import wifi_scanner

# Intentar importar el módulo de visualización, pero continuar si no está disponible
try:
    import wifi_visualizer
    VISUALIZER_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA: No se pudo importar el módulo de visualización. Las funciones de gráficos no estarán disponibles.")
    VISUALIZER_AVAILABLE = False

# Intentar importar el módulo de base de datos, pero continuar si no está disponible
try:
    import wifi_db
    DB_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA: No se pudo importar el módulo de base de datos. El almacenamiento en MongoDB no estará disponible.")
    DB_AVAILABLE = False

# Intentar importar el módulo de tendencias, pero continuar si no está disponible
try:
    import wifi_trends
    TRENDS_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA: No se pudo importar el módulo de tendencias. El análisis de tendencias no estará disponible.")
    TRENDS_AVAILABLE = False

def ensure_wifi_interface_up():
    """
    Asegura que la interfaz WiFi esté activa.

    Returns:
        bool: True si la interfaz está activa, False en caso contrario
    """
    try:
        # Verificar si la interfaz existe
        print("Verificando interfaces WiFi disponibles...")
        iw_dev = subprocess.run(["sudo", "iw", "dev"],
                               capture_output=True, text=True, check=True)
        print(f"Interfaces disponibles:\n{iw_dev.stdout}")

        if "wlan0" not in iw_dev.stdout:
            print("¡ADVERTENCIA! No se encontró la interfaz wlan0.")
            return False

        # Verificar si la interfaz está bloqueada por RF-kill
        print("Verificando estado de RF-kill...")
        rfkill_result = subprocess.run(["sudo", "rfkill", "list"],
                               capture_output=True, text=True, check=True)
        print(f"Estado de RF-kill:\n{rfkill_result.stdout}")

        if "Soft blocked: yes" in rfkill_result.stdout:
            print("Desbloqueando interfaz WiFi...")
            subprocess.run(["sudo", "rfkill", "unblock", "wifi"], check=True)
            time.sleep(1)

        # Desactivar la interfaz primero
        print("Desactivando interfaz wlan0...")
        subprocess.run(["sudo", "ip", "link", "set", "wlan0", "down"], check=True)
        time.sleep(1)

        # Activar la interfaz
        print("Activando interfaz wlan0...")
        subprocess.run(["sudo", "ip", "link", "set", "wlan0", "up"], check=True)

        # Esperar a que la interfaz esté lista
        print("Esperando a que la interfaz esté lista...")
        time.sleep(3)

        # Verificar estado
        print("Verificando estado de la interfaz...")
        link_result = subprocess.run(["ip", "link", "show", "wlan0"],
                               capture_output=True, text=True, check=True)
        print(f"Estado de la interfaz:\n{link_result.stdout}")

        # Probar un escaneo directamente
        print("Intentando escaneo de prueba...")
        try:
            scan_result = subprocess.run(["sudo", "iwlist", "wlan0", "scan"],
                                  capture_output=True, text=True, check=True, timeout=10)
            print("Escaneo de prueba exitoso.")
            return True
        except subprocess.CalledProcessError as scan_error:
            print(f"Error en el escaneo de prueba: {scan_error}")
            print(f"Salida del error: {scan_error.stderr}")
            return False
        except subprocess.TimeoutExpired:
            print("El escaneo de prueba tardó demasiado tiempo. Puede que la interfaz esté ocupada.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error al activar la interfaz WiFi: {e}")
        print(f"Salida del error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def continuous_scan(interval, count, output_dir=None, db=None, use_json=True, generate_graphs=False):
    """
    Realiza escaneos continuos de redes WiFi.

    Args:
        interval (int): Intervalo entre escaneos en segundos
        count (int): Número de escaneos a realizar (0 para infinito)
        output_dir (str, optional): Directorio para guardar los resultados
        db (WiFiDB, optional): Instancia de WiFiDB para guardar en MongoDB
        use_json (bool): Si es True, guarda los resultados en archivos JSON
        generate_graphs (bool): Si es True, genera gráficos PNG
    """
    if output_dir and (use_json or generate_graphs):
        os.makedirs(output_dir, exist_ok=True)

    scan_count = 0
    start_time = datetime.now()

    try:
        while count == 0 or scan_count < count:
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            elapsed_seconds = elapsed_time.total_seconds()
            elapsed_minutes = elapsed_seconds / 60
            elapsed_hours = elapsed_minutes / 60

            print(f"\n--- Escaneo #{scan_count + 1} (Tiempo transcurrido: {int(elapsed_hours)}h {int(elapsed_minutes % 60)}m {int(elapsed_seconds % 60)}s) ---")
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")

            # Realizar escaneo
            networks = wifi_scanner.scan_wifi()

            if networks:
                # Guardar en MongoDB si está disponible
                if db and db.is_connected():
                    metadata = {
                        "source": "continuous_scan",
                        "scan_number": scan_count + 1,
                        "interval": interval,
                        "start_time": start_time.isoformat()
                    }
                    scan_id = db.save_scan(networks, metadata=metadata)
                    if scan_id:
                        print(f"Datos guardados en MongoDB con ID: {scan_id}")

                # Guardar resultados en archivo JSON si se solicitó
                if use_json:
                    if output_dir:
                        json_file = os.path.join(output_dir, f"wifi_scan_{timestamp}.json")
                    else:
                        json_file = f"wifi_scan_{timestamp}.json"

                    wifi_scanner.save_scan_results(networks, json_file)
                    print(f"Datos guardados en archivo JSON: {json_file}")

                # Generar gráficos si se solicitó y el visualizador está disponible
                if generate_graphs and VISUALIZER_AVAILABLE:
                    try:
                        print("Generando gráficos...")
                        if output_dir:
                            channel_graph_file = os.path.join(output_dir, f"wifi_channel_graph_{timestamp}.png")
                            network_list_file = os.path.join(output_dir, f"wifi_network_list_{timestamp}.png")
                        else:
                            channel_graph_file = f"wifi_channel_graph_{timestamp}.png"
                            network_list_file = f"wifi_network_list_{timestamp}.png"

                        wifi_visualizer.plot_channel_graph(networks, channel_graph_file)
                        wifi_visualizer.plot_network_list(networks, network_list_file)
                        print(f"Gráficos guardados: {channel_graph_file}, {network_list_file}")
                    except Exception as e:
                        print(f"Error al generar gráficos: {e}")
                elif generate_graphs and not VISUALIZER_AVAILABLE:
                    print("No se generarán gráficos porque el módulo de visualización no está disponible.")

            scan_count += 1

            # Mostrar estadísticas si se han realizado múltiples escaneos y se usa MongoDB
            if scan_count > 1 and db and db.is_connected():
                try:
                    # Obtener estadísticas básicas
                    total_networks = db.collection.count_documents({"timestamp": {"$gte": start_time}})
                    unique_networks = len(db.collection.distinct("networks.essid", {"timestamp": {"$gte": start_time}}))
                    print(f"Estadísticas: {scan_count} escaneos, {total_networks} redes detectadas, {unique_networks} redes únicas")
                except Exception as e:
                    print(f"Error al obtener estadísticas: {e}")

            # Esperar para el siguiente escaneo
            if count == 0 or scan_count < count:
                print(f"Esperando {interval} segundos para el siguiente escaneo...")
                time.sleep(interval)

    except KeyboardInterrupt:
        print("\nEscaneo detenido por el usuario.")

        # Mostrar resumen final si se usa MongoDB
        if db and db.is_connected():
            try:
                end_time = datetime.now()
                elapsed_time = end_time - start_time
                elapsed_seconds = elapsed_time.total_seconds()

                total_networks = db.collection.count_documents({"timestamp": {"$gte": start_time, "$lte": end_time}})
                unique_networks = len(db.collection.distinct("networks.essid", {"timestamp": {"$gte": start_time, "$lte": end_time}}))

                print(f"\nResumen de la sesión:")
                print(f"- Duración: {int(elapsed_seconds // 3600)}h {int((elapsed_seconds % 3600) // 60)}m {int(elapsed_seconds % 60)}s")
                print(f"- Escaneos realizados: {scan_count}")
                print(f"- Total de redes detectadas: {total_networks}")
                print(f"- Redes únicas detectadas: {unique_networks}")

                if TRENDS_AVAILABLE:
                    print("\nPara visualizar tendencias, ejecute:")
                    print(f"python wifi_analyzer.py --use-mongodb --trends --days {max(1, int(elapsed_seconds / 86400) + 1)}")
            except Exception as e:
                print(f"Error al generar resumen: {e}")
        else:
            # Mostrar resumen básico si no se usa MongoDB
            end_time = datetime.now()
            elapsed_time = end_time - start_time
            elapsed_seconds = elapsed_time.total_seconds()

            print(f"\nResumen de la sesión:")
            print(f"- Duración: {int(elapsed_seconds // 3600)}h {int((elapsed_seconds % 3600) // 60)}m {int(elapsed_seconds % 60)}s")
            print(f"- Escaneos realizados: {scan_count}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Analizador de redes WiFi para Raspberry Pi')

    # Opciones básicas
    parser.add_argument('--scan', action='store_true', help='Realizar un único escaneo')
    parser.add_argument('--visualize', action='store_true', help='Visualizar el último escaneo')
    parser.add_argument('--continuous', action='store_true', help='Realizar escaneos continuos')
    parser.add_argument('--interval', type=int, default=60, help='Intervalo entre escaneos (segundos)')
    parser.add_argument('--count', type=int, default=0, help='Número de escaneos (0 para infinito)')
    parser.add_argument('--output-dir', type=str, help='Directorio para guardar los resultados')

    # Opciones de almacenamiento
    storage_group = parser.add_mutually_exclusive_group()
    storage_group.add_argument('--use-json', action='store_true', help='Usar archivos JSON para almacenar los resultados (predeterminado)')
    storage_group.add_argument('--use-mongodb', action='store_true', help='Usar MongoDB para almacenar los resultados')

    # Opciones de visualización
    parser.add_argument('--generate-graphs', action='store_true', help='Generar gráficos PNG de los resultados')

    # Opciones de MongoDB
    parser.add_argument('--mongo-host', type=str, default='localhost', help='Host de MongoDB')
    parser.add_argument('--mongo-port', type=int, default=27017, help='Puerto de MongoDB')
    parser.add_argument('--mongo-db', type=str, default='wifi_analyzer', help='Nombre de la base de datos MongoDB')
    parser.add_argument('--import-json', action='store_true', help='Importar archivos JSON existentes a MongoDB')
    parser.add_argument('--trends', action='store_true', help='Generar gráficos de tendencias desde MongoDB')
    parser.add_argument('--days', type=int, default=1, help='Número de días para análisis de tendencias')
    parser.add_argument('--network', type=str, help='Nombre de la red para análisis específico de tendencias')

    args = parser.parse_args()

    # Inicializar conexión a MongoDB si se solicita
    db = None
    if args.use_mongodb and DB_AVAILABLE:
        try:
            print(f"Conectando a MongoDB ({args.mongo_host}:{args.mongo_port})...")
            db = wifi_db.WiFiDB(host=args.mongo_host, port=args.mongo_port, db_name=args.mongo_db)
            if not db.is_connected():
                print("No se pudo conectar a MongoDB. Se usará almacenamiento en archivos JSON.")
                db = None
        except Exception as e:
            print(f"Error al conectar a MongoDB: {e}")
            print("Se usará almacenamiento en archivos JSON.")
            db = None
    elif args.use_mongodb and not DB_AVAILABLE:
        print("El módulo de base de datos no está disponible. Se usará almacenamiento en archivos JSON.")

    # Importar archivos JSON existentes a MongoDB
    if args.import_json and db and db.is_connected():
        print("Importando archivos JSON existentes a MongoDB...")
        imported = wifi_db.import_existing_scans(directory=args.output_dir or '.', db=db)
        print(f"Se importaron {imported} archivos.")
        return

    # Asegurar que la interfaz WiFi esté activa
    if not ensure_wifi_interface_up():
        print("No se pudo activar la interfaz WiFi. Verifique los permisos y el hardware.")
        return

    # Generar gráficos de tendencias desde MongoDB
    if args.trends and db and db.is_connected():
        if not TRENDS_AVAILABLE:
            print("El módulo de tendencias no está disponible. No se pueden generar gráficos de tendencias.")
            return

        print(f"Generando gráficos de tendencias de los últimos {args.days} días...")
        end_time = datetime.now()
        start_time = end_time - timedelta(days=args.days)

        try:
            # Obtener datos de MongoDB
            scans = db.get_scans_in_timeframe(start_time, end_time)

            if not scans:
                print(f"No se encontraron datos en el período especificado ({start_time} a {end_time}).")
                return

            print(f"Se encontraron {len(scans)} escaneos en el período especificado.")

            # Generar gráficos de tendencias
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = args.output_dir or '.'

                # Generar gráfico de ocupación de canales
                channel_trend_file = os.path.join(output_dir, f"wifi_channel_trend_{timestamp}.png")
                wifi_trends.generate_channel_occupancy_trend(db, args.days, channel_trend_file)

                # Generar gráfico de número de redes
                network_count_file = os.path.join(output_dir, f"wifi_network_count_trend_{timestamp}.png")
                wifi_trends.generate_network_count_trend(db, args.days, network_count_file)

                # Si se especificó una red, generar gráfico de intensidad de señal
                if args.network:
                    signal_trend_file = os.path.join(output_dir, f"wifi_signal_trend_{args.network}_{timestamp}.png")
                    wifi_trends.generate_signal_strength_trend(db, args.network, None, args.days, signal_trend_file)

                print(f"Análisis de tendencias completado. Los gráficos se guardaron en {output_dir}")
            except Exception as e:
                print(f"Error al generar gráficos de tendencias: {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"Error al obtener datos para tendencias: {e}")

        return

    # Ejecutar la acción correspondiente
    if args.scan:
        print("Realizando un único escaneo...")
        networks = wifi_scanner.scan_wifi()
        if networks:
            # Determinar el modo de almacenamiento
            use_mongodb = args.use_mongodb and DB_AVAILABLE
            use_json = args.use_json or (not use_mongodb)

            json_file = None
            scan_id = None

            # Guardar en MongoDB si se solicitó
            if use_mongodb and db and db.is_connected():
                scan_id = db.save_scan(networks, metadata={"source": "single_scan"})
                if scan_id:
                    print(f"Datos guardados en MongoDB con ID: {scan_id}")

            # Guardar en archivo JSON si se solicitó o es el modo predeterminado
            if use_json:
                json_file = wifi_scanner.save_scan_results(networks)
                print(f"Datos guardados en archivo JSON: {json_file}")

            # Generar gráficos si se solicitó explícitamente y el visualizador está disponible
            if args.generate_graphs and VISUALIZER_AVAILABLE:
                try:
                    print("Generando gráficos...")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    if args.output_dir:
                        os.makedirs(args.output_dir, exist_ok=True)
                        channel_graph_file = os.path.join(args.output_dir, f"wifi_channel_graph_{timestamp}.png")
                        network_list_file = os.path.join(args.output_dir, f"wifi_network_list_{timestamp}.png")
                    else:
                        channel_graph_file = f"wifi_channel_graph_{timestamp}.png"
                        network_list_file = f"wifi_network_list_{timestamp}.png"

                    wifi_visualizer.plot_channel_graph(networks, channel_graph_file)
                    wifi_visualizer.plot_network_list(networks, network_list_file)
                except Exception as e:
                    print(f"Error al generar gráficos: {e}")
            elif args.generate_graphs and not VISUALIZER_AVAILABLE:
                print("No se generarán gráficos porque el módulo de visualización no está disponible.")

    elif args.visualize:
        if VISUALIZER_AVAILABLE:
            print("Visualizando el último escaneo...")
            try:
                # Si MongoDB está disponible y se solicitó, intentar obtener el último escaneo de allí
                if args.use_mongodb and db and db.is_connected():
                    latest_scan = db.get_latest_scan()
                    if latest_scan:
                        print(f"Visualizando escaneo de MongoDB del {latest_scan['timestamp']}")
                        # Aquí podríamos implementar una visualización específica para datos de MongoDB
                        # Por ahora, usamos la visualización estándar
                        wifi_visualizer.main()
                    else:
                        print("No se encontraron escaneos en MongoDB.")
                else:
                    # Usar la visualización estándar basada en archivos JSON
                    wifi_visualizer.main()
            except Exception as e:
                print(f"Error al visualizar el escaneo: {e}")
        else:
            print("La visualización no está disponible porque el módulo de visualización no se pudo cargar.")

    elif args.continuous:
        print(f"Iniciando escaneo continuo cada {args.interval} segundos...")
        # Determinar el modo de almacenamiento para el escaneo continuo
        use_mongodb = args.use_mongodb and DB_AVAILABLE
        use_json = args.use_json or (not use_mongodb)

        # Pasar los parámetros de almacenamiento a la función de escaneo continuo
        continuous_scan(args.interval, args.count, args.output_dir,
                       db if use_mongodb else None,
                       use_json,
                       args.generate_graphs)

    else:
        # Si no se especifica ninguna acción, mostrar ayuda
        parser.print_help()

    # Cerrar conexión a MongoDB si está abierta
    if db:
        db.close()

if __name__ == "__main__":
    main()
