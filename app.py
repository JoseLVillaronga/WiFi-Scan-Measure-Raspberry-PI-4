#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicación web para WiFi Analyzer
"""

import os
import json
import pytz
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.objectid import ObjectId

# Importar módulos propios
import wifi_scanner
from config import Config

# Inicializar la aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Configurar MongoDB
mongo = PyMongo(app)

# Rutas de la aplicación
@app.route('/')
def index():
    """Página principal con dashboard"""
    return render_template('index.html')

@app.route('/scan')
def scan_page():
    """Página para realizar escaneos"""
    return render_template('scan.html')

@app.route('/history')
def history_page():
    """Página para ver el historial de escaneos"""
    page = request.args.get('page', 1, type=int)
    limit = app.config['ITEMS_PER_PAGE']
    skip = (page - 1) * limit

    # Obtener el total de escaneos
    total = mongo.db.wifi_scans.count_documents({})

    # Obtener los escaneos paginados
    scans = list(mongo.db.wifi_scans.find().sort('timestamp', -1).skip(skip).limit(limit))

    # Calcular el número total de páginas
    total_pages = (total + limit - 1) // limit

    return render_template('history.html',
                          scans=scans,
                          page=page,
                          total_pages=total_pages,
                          total_scans=total)

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """API para realizar un escaneo"""
    try:
        # Obtener parámetros
        # Usar zona horaria configurada
        local_tz = pytz.timezone(app.config['TIMEZONE'])
        now = datetime.now(local_tz)

        scan_name = request.form.get('scan_name', f"Escaneo {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Realizar escaneo
        networks = wifi_scanner.scan_wifi()

        if networks:
            # Guardar en MongoDB
            result = mongo.db.wifi_scans.insert_one({
                'name': scan_name,
                'timestamp': now,
                'networks': networks,
                'total_networks': len(networks),
                'metadata': {
                    'source': 'web_interface'
                }
            })

            return jsonify({
                'success': True,
                'message': 'Escaneo completado con éxito',
                'scan_id': str(result.inserted_id),
                'networks_found': len(networks)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No se encontraron redes WiFi o hubo un error en el escaneo'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al realizar el escaneo: {str(e)}'
        }), 500

@app.route('/api/scans', methods=['GET'])
def api_get_scans():
    """API para obtener la lista de escaneos"""
    try:
        # Obtener parámetros de paginación
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['ITEMS_PER_PAGE'], type=int)
        skip = (page - 1) * limit

        # Obtener el total de escaneos
        total = mongo.db.wifi_scans.count_documents({})

        # Obtener los escaneos paginados
        scans = list(mongo.db.wifi_scans.find({}, {
            'name': 1,
            'timestamp': 1,
            'total_networks': 1
        }).sort('timestamp', -1).skip(skip).limit(limit))

        # Convertir ObjectId a string para serialización JSON
        for scan in scans:
            scan['_id'] = str(scan['_id'])

        return jsonify({
            'success': True,
            'total': total,
            'page': page,
            'limit': limit,
            'scans': scans
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener los escaneos: {str(e)}'
        }), 500

@app.route('/api/scans/<scan_id>', methods=['GET'])
def api_get_scan(scan_id):
    """API para obtener un escaneo específico"""
    try:
        # Convertir string a ObjectId
        scan = mongo.db.wifi_scans.find_one({'_id': ObjectId(scan_id)})

        if scan:
            # Convertir a JSON serializable
            scan_json = json.loads(dumps(scan))

            return jsonify({
                'success': True,
                'scan': scan_json
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Escaneo no encontrado'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener el escaneo: {str(e)}'
        }), 500

@app.route('/api/networks/channels', methods=['GET'])
def api_networks_by_channel():
    """API para obtener estadísticas de redes por canal"""
    try:
        # Obtener el último escaneo
        last_scan = mongo.db.wifi_scans.find_one(sort=[('timestamp', -1)])

        if not last_scan:
            return jsonify({
                'success': False,
                'message': 'No hay escaneos disponibles'
            }), 404

        # Contar redes por canal
        channels_2g = {}
        channels_5g = {}

        for network in last_scan['networks']:
            channel = network.get('channel')
            if channel:
                if channel <= 14:  # 2.4GHz
                    channels_2g[channel] = channels_2g.get(channel, 0) + 1
                else:  # 5GHz
                    channels_5g[channel] = channels_5g.get(channel, 0) + 1

        # Convertir timestamp a formato ISO para que sea serializable
        timestamp_iso = last_scan['timestamp'].isoformat()

        return jsonify({
            'success': True,
            'timestamp': timestamp_iso,
            'channels_2g': channels_2g,
            'channels_5g': channels_5g
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener estadísticas de canales: {str(e)}'
        }), 500

@app.route('/api/networks/signal', methods=['GET'])
def api_networks_by_signal():
    """API para obtener las redes con mejor señal"""
    try:
        # Obtener el último escaneo
        last_scan = mongo.db.wifi_scans.find_one(sort=[('timestamp', -1)])

        if not last_scan:
            return jsonify({
                'success': False,
                'message': 'No hay escaneos disponibles'
            }), 404

        # Ordenar redes por intensidad de señal
        networks = sorted(last_scan['networks'], key=lambda x: x.get('signal', -100), reverse=True)

        # Limitar a las mejores redes
        top_networks = networks[:app.config['MAX_NETWORKS_IN_CHART']]

        # Convertir timestamp a formato ISO para que sea serializable
        timestamp_iso = last_scan['timestamp'].isoformat()

        return jsonify({
            'success': True,
            'timestamp': timestamp_iso,
            'networks': top_networks
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener redes por señal: {str(e)}'
        }), 500

@app.route('/api/networks/trend/<essid>', methods=['GET'])
def api_network_trend(essid):
    """API para obtener la tendencia de señal de una red específica"""
    try:
        # Obtener parámetros
        days = request.args.get('days', 1, type=int)

        # Calcular rango de tiempo con zona horaria configurada
        local_tz = pytz.timezone(app.config['TIMEZONE'])
        end_time = datetime.now(local_tz)
        start_time = end_time - timedelta(days=days)

        # Buscar la red en los escaneos
        pipeline = [
            {'$match': {'timestamp': {'$gte': start_time, '$lte': end_time}}},
            {'$unwind': '$networks'},
            {'$match': {'networks.essid': essid}},
            {'$project': {
                '_id': 0,
                'timestamp': 1,
                'signal': '$networks.signal',
                'channel': '$networks.channel'
            }},
            {'$sort': {'timestamp': 1}}
        ]

        results = list(mongo.db.wifi_scans.aggregate(pipeline))

        if not results:
            return jsonify({
                'success': False,
                'message': f'No se encontraron datos para la red {essid}'
            }), 404

        return jsonify({
            'success': True,
            'essid': essid,
            'data': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener tendencia de red: {str(e)}'
        }), 500

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
