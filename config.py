#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuración para la aplicación WiFi Analyzer
"""

import os

# Configuración de la aplicación Flask
class Config:
    # Configuración general
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-predeterminada'
    DEBUG = os.environ.get('FLASK_DEBUG') or True

    # Configuración de MongoDB
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/wifi_analyzer'
    MONGO_DBNAME = 'wifi_analyzer'

    # Configuración de escaneo WiFi
    DEFAULT_SCAN_INTERVAL = 60  # segundos
    DEFAULT_SCAN_COUNT = 1

    # Configuración de la interfaz
    ITEMS_PER_PAGE = 10
    MAX_NETWORKS_IN_CHART = 10

    # Configuración de zona horaria
    TIMEZONE = 'America/Argentina/Buenos_Aires'  # Zona horaria para Argentina (UTC-3)

    # Rutas de archivos
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_EXTENSIONS = {'json'}

    # Asegurar que exista el directorio de uploads
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
