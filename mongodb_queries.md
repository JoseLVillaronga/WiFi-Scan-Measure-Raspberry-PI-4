# Consultas útiles de MongoDB para WiFi Analyzer

Este documento contiene consultas útiles para explorar y analizar los datos de WiFi Analyzer almacenados en MongoDB.

## Conexión a MongoDB

Para conectarse a MongoDB, ejecute:

```bash
mongosh
```

## Consultas básicas

### Ver bases de datos disponibles

```javascript
show databases
```

### Cambiar a la base de datos wifi_analyzer

```javascript
use wifi_analyzer
```

### Ver colecciones disponibles

```javascript
show collections
```

## Consultas de escaneos WiFi

### Contar el número total de escaneos

```javascript
db.wifi_scans.count()
```

Nota: Este comando está obsoleto. Se recomienda usar:

```javascript
db.wifi_scans.countDocuments()
```

### Ver el último escaneo

```javascript
db.wifi_scans.find().sort({timestamp: -1}).limit(1).pretty()
```

### Ver todos los nombres de redes WiFi (ESSID) únicos

```javascript
db.wifi_scans.distinct("networks.essid")
```

### Contar escaneos de las últimas 24 horas

```javascript
db.wifi_scans.find({
  timestamp: {
    $gte: new Date(new Date().getTime() - 24 * 60 * 60 * 1000)
  }
}).count()
```

## Consultas avanzadas

### Buscar una red WiFi específica por nombre

```javascript
db.wifi_scans.find({"networks.essid": "Nombre de la Red"}).pretty()
```

### Encontrar redes con señal fuerte (mejor que -60 dBm)

```javascript
db.wifi_scans.find({"networks.signal": {$gt: -60}}).pretty()
```

### Encontrar redes en un canal específico

```javascript
db.wifi_scans.find({"networks.channel": 6}).pretty()
```

### Encontrar redes en la banda de 5GHz

```javascript
db.wifi_scans.find({"networks.channel": {$gt: 14}}).pretty()
```

### Encontrar redes no encriptadas

```javascript
db.wifi_scans.find({"networks.encrypted": false}).pretty()
```

## Análisis de tendencias

### Evolución de la intensidad de señal de una red específica

```javascript
db.wifi_scans.aggregate([
  {$match: {"networks.essid": "Nombre de la Red"}},
  {$unwind: "$networks"},
  {$match: {"networks.essid": "Nombre de la Red"}},
  {$project: {
    _id: 0,
    timestamp: 1,
    signal: "$networks.signal",
    channel: "$networks.channel"
  }},
  {$sort: {timestamp: 1}}
])
```

### Contar redes por canal

```javascript
db.wifi_scans.aggregate([
  {$unwind: "$networks"},
  {$group: {
    _id: "$networks.channel",
    count: {$sum: 1}
  }},
  {$sort: {_id: 1}}
])
```

### Promedio de intensidad de señal por red

```javascript
db.wifi_scans.aggregate([
  {$unwind: "$networks"},
  {$group: {
    _id: "$networks.essid",
    avgSignal: {$avg: "$networks.signal"},
    count: {$sum: 1}
  }},
  {$sort: {avgSignal: -1}}
])
```

## Exportación de datos

### Exportar todos los escaneos a un archivo JSON

Desde la línea de comandos (fuera de mongosh):

```bash
mongoexport --db wifi_analyzer --collection wifi_scans --out wifi_data.json
```

### Exportar resultados de una consulta específica

```bash
mongoexport --db wifi_analyzer --collection wifi_scans --query '{"networks.essid":"Nombre de la Red"}' --out red_especifica.json
```

## Mantenimiento de la base de datos

### Eliminar escaneos antiguos (más de 30 días)

```javascript
db.wifi_scans.deleteMany({
  timestamp: {
    $lt: new Date(new Date().getTime() - 30 * 24 * 60 * 60 * 1000)
  }
})
```

### Crear índice para mejorar el rendimiento de las consultas

```javascript
db.wifi_scans.createIndex({timestamp: -1})
db.wifi_scans.createIndex({"networks.essid": 1})
db.wifi_scans.createIndex({"networks.signal": 1})
```

### Ver índices existentes

```javascript
db.wifi_scans.getIndexes()
```
