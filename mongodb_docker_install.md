# Instalación de MongoDB en Raspberry Pi 4 usando Docker

Para Raspberry Pi 4 con Debian 12, una forma sencilla y efectiva de instalar MongoDB es utilizando Docker. Este método evita problemas de compatibilidad con la arquitectura ARM y simplifica la configuración.

## Requisitos previos

- Raspberry Pi 4 con Debian 12
- Docker instalado (si no lo tienes, instálalo con `sudo apt install docker.io`)
- Permisos de superusuario (sudo)

## Pasos para instalar MongoDB

### 1. Ejecutar MongoDB en Docker

```bash
sudo docker run -d \
  --name mongodb \
  --network host \
  mongo:4.4.18
```

Este comando:
- Descarga la imagen de MongoDB 4.4.18 (versión estable para ARM)
- Crea un contenedor llamado "mongodb"
- Utiliza la red del host para que MongoDB sea accesible en localhost:27017
- Ejecuta MongoDB en segundo plano (-d)

### 2. Verificar que el contenedor está en ejecución

```bash
sudo docker ps --filter name=mongodb
```

Deberías ver una salida similar a:
```
CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS         PORTS     NAMES
a0bf0a33aaca   mongo:4.4.18   "docker-entrypoint.s…"   14 seconds ago   Up 9 seconds             mongodb
```

### 3. Verificar los logs de MongoDB

```bash
sudo docker logs mongodb
```

Verás algunos mensajes de advertencia sobre ARMv8.2-A, pero MongoDB 4.4.18 funciona correctamente en Raspberry Pi 4.

### 4. Instalar el cliente MongoDB Shell (mongosh)

```bash
sudo apt install mongodb-mongosh
```

### 5. Conectarse a MongoDB

```bash
mongosh
```

Deberías ver una salida similar a:
```
Current Mongosh Log ID: 6826394a3dc0af0f82d2950c
Connecting to:          mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.5.1
Using MongoDB:          4.4.18
Using Mongosh:          2.5.1
```

### 6. Verificar las bases de datos disponibles

En el shell de MongoDB, ejecuta:
```
show databases
```

Deberías ver las bases de datos predeterminadas:
```
admin   40.00 KiB
config  12.00 KiB
local   40.00 KiB
```

### 7. Salir del shell de MongoDB

```
quit
```

## Configuración para WiFi Analyzer

Para usar MongoDB con el WiFi Analyzer, simplemente ejecuta:

```bash
python wifi_analyzer.py --use-mongodb --scan
```

El programa se conectará automáticamente a MongoDB en localhost:27017 sin autenticación.

## Ventajas de usar Docker para MongoDB

1. **Fácil instalación**: No hay problemas de dependencias o incompatibilidades con la arquitectura ARM
2. **Sin contraseña**: Por defecto, se ejecuta sin autenticación
3. **Vinculado a localhost**: Accesible solo desde la propia Raspberry Pi
4. **Fácil mantenimiento**: Puedes actualizar, reiniciar o eliminar el contenedor sin afectar al sistema
5. **Persistencia de datos**: Los datos se almacenan en el volumen de Docker

## Comandos útiles para gestionar MongoDB en Docker

### Detener MongoDB
```bash
sudo docker stop mongodb
```

### Iniciar MongoDB (después de detenerlo)
```bash
sudo docker start mongodb
```

### Reiniciar MongoDB
```bash
sudo docker restart mongodb
```

### Eliminar el contenedor de MongoDB
```bash
sudo docker rm -f mongodb
```

### Configurar MongoDB para que se inicie automáticamente
```bash
sudo docker update --restart=always mongodb
```

Con esta configuración, MongoDB estará disponible en `localhost:27017` sin autenticación, exactamente como necesitas para el proyecto WiFi Analyzer.
