#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi Database para Raspberry Pi
Este módulo maneja la conexión a MongoDB y las operaciones de base de datos
para almacenar y recuperar datos de escaneos WiFi.
"""

import os
import json
from datetime import datetime
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configuración de MongoDB
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))
MONGO_DB = os.environ.get('MONGO_DB', 'wifi_analyzer')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'wifi_scans')

# Configuración para MongoDB sin autenticación
MONGO_USE_AUTH = False  # Cambiar a True si se configura autenticación en el futuro
MONGO_USER = os.environ.get('MONGO_USER', '')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', '')

class WiFiDB:
    """Clase para manejar operaciones de base de datos para WiFi Analyzer"""

    def __init__(self, host=MONGO_HOST, port=MONGO_PORT, db_name=MONGO_DB, collection_name=MONGO_COLLECTION):
        """
        Inicializa la conexión a MongoDB.

        Args:
            host (str): Host de MongoDB
            port (int): Puerto de MongoDB
            db_name (str): Nombre de la base de datos
            collection_name (str): Nombre de la colección
        """
        self.client = None
        self.db = None
        self.collection = None
        self.host = host
        self.port = port
        self.db_name = db_name
        self.collection_name = collection_name

        # Intentar conectar a MongoDB
        self.connect()

    def connect(self):
        """Establece la conexión a MongoDB"""
        try:
            # Construir la URI de conexión
            if MONGO_USE_AUTH and MONGO_USER and MONGO_PASSWORD:
                # Con autenticación
                uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{self.host}:{self.port}/{self.db_name}"
                self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            else:
                # Sin autenticación
                self.client = MongoClient(self.host, self.port, serverSelectionTimeoutMS=5000)

            # Verificar la conexión
            self.client.server_info()
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            print(f"Conexión exitosa a MongoDB ({self.host}:{self.port}, DB: {self.db_name})")

            # Crear índices para mejorar el rendimiento de las consultas
            try:
                self.collection.create_index([("timestamp", pymongo.DESCENDING)])
                self.collection.create_index([("networks.essid", pymongo.TEXT)])
            except Exception as index_error:
                print(f"Advertencia: No se pudieron crear índices: {index_error}")
                print("Esto no afectará la funcionalidad básica, pero puede impactar el rendimiento.")

            return True
        except pymongo.errors.ServerSelectionTimeoutError as e:
            print(f"Error al conectar a MongoDB: {e}")
            print("Asegúrese de que MongoDB esté instalado y en ejecución.")
            return False
        except Exception as e:
            print(f"Error inesperado al conectar a MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False

    def is_connected(self):
        """Verifica si la conexión a MongoDB está activa"""
        if not self.client:
            return False
        try:
            self.client.server_info()
            return True
        except:
            return False

    def save_scan(self, networks, metadata=None):
        """
        Guarda los resultados de un escaneo en MongoDB.

        Args:
            networks (list): Lista de redes WiFi
            metadata (dict, optional): Metadatos adicionales

        Returns:
            str: ID del documento insertado o None si hay un error
        """
        if not self.is_connected():
            if not self.connect():
                print("No se pudo conectar a MongoDB. Los datos no se guardarán.")
                return None

        try:
            # Crear documento
            timestamp = datetime.now()
            document = {
                "timestamp": timestamp,
                "networks": networks,
                "total_networks": len(networks)
            }

            # Añadir metadatos si existen
            if metadata:
                document["metadata"] = metadata

            # Insertar en la base de datos
            result = self.collection.insert_one(document)

            print(f"Datos guardados en MongoDB con ID: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            print(f"Error al guardar datos en MongoDB: {e}")
            return None

    def get_scan(self, scan_id):
        """
        Recupera un escaneo específico por su ID.

        Args:
            scan_id (str): ID del escaneo

        Returns:
            dict: Documento del escaneo o None si no se encuentra
        """
        if not self.is_connected():
            if not self.connect():
                return None

        try:
            result = self.collection.find_one({"_id": ObjectId(scan_id)})
            return result
        except Exception as e:
            print(f"Error al recuperar escaneo {scan_id}: {e}")
            return None

    def get_latest_scan(self):
        """
        Recupera el escaneo más reciente.

        Returns:
            dict: Documento del escaneo más reciente o None si no hay escaneos
        """
        if not self.is_connected():
            if not self.connect():
                return None

        try:
            result = self.collection.find_one(sort=[("timestamp", pymongo.DESCENDING)])
            return result
        except Exception as e:
            print(f"Error al recuperar el escaneo más reciente: {e}")
            return None

    def get_scans_in_timeframe(self, start_time, end_time=None):
        """
        Recupera escaneos en un rango de tiempo.

        Args:
            start_time (datetime): Tiempo de inicio
            end_time (datetime, optional): Tiempo de fin. Si es None, se usa el tiempo actual.

        Returns:
            list: Lista de documentos de escaneos
        """
        if not self.is_connected():
            if not self.connect():
                return []

        if end_time is None:
            end_time = datetime.now()

        try:
            query = {"timestamp": {"$gte": start_time, "$lte": end_time}}
            results = list(self.collection.find(query).sort("timestamp", pymongo.ASCENDING))
            return results
        except Exception as e:
            print(f"Error al recuperar escaneos en el rango de tiempo: {e}")
            return []

    def get_network_history(self, essid, mac=None, start_time=None, end_time=None):
        """
        Recupera el historial de una red específica.

        Args:
            essid (str): ESSID de la red
            mac (str, optional): Dirección MAC de la red
            start_time (datetime, optional): Tiempo de inicio
            end_time (datetime, optional): Tiempo de fin

        Returns:
            list: Lista de documentos con la red específica
        """
        if not self.is_connected():
            if not self.connect():
                return []

        query = {}

        # Filtrar por tiempo si se especifica
        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time

        # Filtrar por ESSID y/o MAC
        network_query = {}
        if essid:
            network_query["networks.essid"] = essid
        if mac:
            network_query["networks.mac"] = mac

        # Combinar consultas
        if network_query:
            query.update(network_query)

        try:
            # Usar agregación para extraer solo la red específica de cada escaneo
            pipeline = [
                {"$match": query},
                {"$unwind": "$networks"},
                {"$match": {"networks.essid": essid} if essid else {}},
                {"$match": {"networks.mac": mac} if mac else {}},
                {"$sort": {"timestamp": 1}},
                {"$project": {
                    "timestamp": 1,
                    "network": "$networks",
                    "_id": 0
                }}
            ]

            results = list(self.collection.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"Error al recuperar historial de red: {e}")
            return []

    def export_to_json(self, scan_id, filename=None):
        """
        Exporta un escaneo a un archivo JSON.

        Args:
            scan_id (str): ID del escaneo
            filename (str, optional): Nombre del archivo. Si es None, se genera automáticamente.

        Returns:
            str: Ruta del archivo guardado o None si hay un error
        """
        scan = self.get_scan(scan_id)
        if not scan:
            return None

        if filename is None:
            timestamp = scan["timestamp"].strftime("%Y%m%d_%H%M%S")
            filename = f"wifi_scan_export_{timestamp}.json"

        try:
            # Convertir ObjectId a string para serialización JSON
            scan["_id"] = str(scan["_id"])

            with open(filename, 'w', encoding='utf-8') as f:
                # Convertir datetime a string
                scan["timestamp"] = scan["timestamp"].isoformat()
                json.dump(scan, f, indent=2)

            print(f"Escaneo exportado a {filename}")
            return filename
        except Exception as e:
            print(f"Error al exportar escaneo a JSON: {e}")
            return None

    def import_from_json(self, filename):
        """
        Importa un escaneo desde un archivo JSON.

        Args:
            filename (str): Ruta del archivo JSON

        Returns:
            str: ID del documento insertado o None si hay un error
        """
        if not self.is_connected():
            if not self.connect():
                return None

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convertir timestamp de string a datetime si es necesario
            if isinstance(data.get("timestamp"), str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])

            # Eliminar _id si existe para evitar conflictos
            if "_id" in data:
                del data["_id"]

            # Insertar en la base de datos
            result = self.collection.insert_one(data)

            print(f"Datos importados a MongoDB con ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error al importar datos desde JSON: {e}")
            return None

    def close(self):
        """Cierra la conexión a MongoDB"""
        if self.client:
            self.client.close()
            print("Conexión a MongoDB cerrada")


# Función para importar escaneos existentes a MongoDB
def import_existing_scans(directory='.', db=None):
    """
    Importa todos los archivos JSON de escaneos existentes a MongoDB.

    Args:
        directory (str): Directorio donde buscar archivos JSON
        db (WiFiDB, optional): Instancia de WiFiDB. Si es None, se crea una nueva.

    Returns:
        int: Número de archivos importados
    """
    if db is None:
        db = WiFiDB()

    if not db.is_connected():
        print("No se pudo conectar a MongoDB. No se importarán los escaneos.")
        return 0

    # Buscar archivos JSON de escaneos
    json_files = [f for f in os.listdir(directory) if f.startswith('wifi_scan_') and f.endswith('.json')]

    imported_count = 0
    for json_file in json_files:
        file_path = os.path.join(directory, json_file)

        try:
            # Leer el archivo JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                networks = json.load(f)

            # Extraer timestamp del nombre del archivo
            timestamp_str = json_file.replace('wifi_scan_', '').replace('.json', '')
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except:
                timestamp = datetime.now()

            # Crear documento
            document = {
                "timestamp": timestamp,
                "networks": networks,
                "total_networks": len(networks),
                "metadata": {
                    "imported_from": json_file
                }
            }

            # Insertar en la base de datos
            result = db.collection.insert_one(document)

            print(f"Archivo {json_file} importado con ID: {result.inserted_id}")
            imported_count += 1

        except Exception as e:
            print(f"Error al importar {json_file}: {e}")

    print(f"Se importaron {imported_count} de {len(json_files)} archivos.")
    return imported_count


if __name__ == "__main__":
    # Ejemplo de uso
    db = WiFiDB()
    if db.is_connected():
        print("Importando escaneos existentes...")
        import_existing_scans(db=db)
        db.close()
    else:
        print("No se pudo conectar a MongoDB. Verifique que el servicio esté en ejecución.")
