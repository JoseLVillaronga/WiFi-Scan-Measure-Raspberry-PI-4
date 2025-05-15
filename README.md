# WiFi Analyzer para Raspberry Pi

Este proyecto utiliza una Raspberry Pi 4 con Debian 12 para analizar redes WiFi en las bandas de 2.4GHz y 5GHz, calcular distancias estimadas basadas en la intensidad de señal (RSSI) y generar visualizaciones gráficas.

## Características

- Escaneo de redes WiFi en bandas de 2.4GHz y 5GHz
- Cálculo de distancia estimada basado en RSSI
- Visualización de canales WiFi y su ocupación
- Visualización de lista de redes con detalles
- Soporte para escaneos continuos con intervalo configurable
- Guardado de resultados en formato JSON y MongoDB
- Generación de gráficos en formato PNG
- Análisis de tendencias a lo largo del tiempo
- Visualización de estadísticas históricas

## Requisitos

- Raspberry Pi 4 (o similar) con Debian 12
- Adaptadores WiFi compatibles con 2.4GHz y 5GHz
- Python 3.6 o superior
- Permisos de superusuario para escanear redes WiFi
- MongoDB (opcional, para almacenamiento y análisis de tendencias)

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/usuario/wifi-test.git
   cd wifi-test
   ```

2. Crear y activar un entorno virtual:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instalar dependencias:
   ```
   pip install matplotlib numpy pandas pymongo
   ```

4. (Opcional) Instalar MongoDB para almacenamiento y análisis de tendencias:

   **Opción A: Usando Docker (recomendado para Raspberry Pi 4)**
   ```
   sudo ./install_mongodb_docker.sh
   ```

   Este script instala Docker si es necesario, ejecuta MongoDB en un contenedor, instala el cliente MongoDB Shell y configura todo para que funcione automáticamente.

   Para más detalles, consulta [mongodb_docker_install.md](mongodb_docker_install.md)

   **Opción B: Instalación nativa**
   ```
   sudo ./install_mongodb_rpi.sh
   ```

   Este script intenta instalar MongoDB desde los repositorios de Debian, lo configura para ejecutarse sin autenticación y vinculado solo a localhost (127.0.0.1).

## Uso

### Escaneo único

Para realizar un único escaneo y generar visualizaciones:

```
python wifi_analyzer.py --scan
```

### Visualizar último escaneo

Para visualizar los resultados del último escaneo:

```
python wifi_analyzer.py --visualize
```

### Escaneo continuo

Para realizar escaneos continuos cada 60 segundos:

```
python wifi_analyzer.py --continuous --interval 60
```

Para realizar un número específico de escaneos:

```
python wifi_analyzer.py --continuous --interval 60 --count 10
```

Para guardar los resultados en un directorio específico:

```
python wifi_analyzer.py --continuous --interval 60 --output-dir ./resultados
```

### Uso con MongoDB

Para usar MongoDB para almacenar los resultados:

```
python wifi_analyzer.py --scan --use-mongodb
```

Para realizar escaneos continuos y guardar en MongoDB:

```
python wifi_analyzer.py --continuous --interval 60 --use-mongodb
```

Para importar archivos JSON existentes a MongoDB:

```
python wifi_analyzer.py --use-mongodb --import-json
```

### Análisis de tendencias

Para generar gráficos de tendencias de los últimos 7 días:

```
python wifi_analyzer.py --use-mongodb --trends --days 7
```

Para generar gráficos de tendencias de una red específica:

```
python wifi_analyzer.py --use-mongodb --trends --days 7 --network "Nombre de la Red"
```

## Cálculo de Distancia

El cálculo de distancia se basa en el modelo de pérdida de propagación logarítmica:

```
d = 10^((TxPower - RSSI) / (10 * n))
```

Donde:
- d = distancia estimada en metros
- TxPower = potencia de transmisión a 1 metro (típicamente entre -30 dBm y -50 dBm)
- RSSI = intensidad de señal recibida en dBm
- n = factor de propagación (2 en espacio libre, 2.7-4 en interiores)

## Estructura del Proyecto

- `wifi_scanner.py`: Módulo para escanear redes WiFi
- `wifi_visualizer.py`: Módulo para generar visualizaciones
- `wifi_analyzer.py`: Script principal que integra las funcionalidades
- `wifi_db.py`: Módulo para interactuar con MongoDB
- `wifi_trends.py`: Módulo para generar análisis de tendencias
- `install_mongodb_docker.sh`: Script para instalar MongoDB con Docker
- `install_mongodb_rpi.sh`: Script alternativo para instalar MongoDB nativamente
- `mongodb_docker_install.md`: Documentación sobre la instalación de MongoDB con Docker
- `mongodb_queries.md`: Consultas útiles para explorar datos en MongoDB
- `calculo_distancia_RSSI.md`: Documentación sobre el cálculo de distancia

## Ejemplos de Visualizaciones

### Gráfico de Canales
![Ejemplo de Gráfico de Canales](./ejemplo_grafico_canales.png)

### Lista de Redes
![Ejemplo de Lista de Redes](./ejemplo_lista_redes.png)

### Gráfico de Tendencias
![Ejemplo de Gráfico de Tendencias](./ejemplo_grafico_tendencias.png)

### Gráfico de Intensidad de Señal
![Ejemplo de Gráfico de Intensidad de Señal](./ejemplo_grafico_intensidad.png)

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abra un issue para discutir los cambios propuestos.
