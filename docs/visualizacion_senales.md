# Documentación: Visualización de Señales WiFi

## Introducción

Este documento explica cómo se visualizan las señales WiFi en la aplicación WiFi Analyzer, específicamente en lo relacionado con la representación gráfica de la intensidad de señal (dBm).

## Valores de intensidad de señal WiFi (dBm)

La intensidad de señal WiFi se mide en dBm (decibelios-milivatio), que es una unidad logarítmica que expresa la relación de potencia en decibelios (dB) referenciada a un milivatio (mW).

Características importantes:
- Los valores de dBm para WiFi son siempre negativos (típicamente entre -30 y -90)
- Valores más cercanos a 0 indican señales más fuertes
- Valores más alejados de 0 (más negativos) indican señales más débiles

Rangos típicos:
- -30 a -50 dBm: Señal excelente
- -50 a -60 dBm: Señal muy buena
- -60 a -70 dBm: Señal buena
- -70 a -80 dBm: Señal aceptable
- -80 a -90 dBm: Señal débil

## Visualización en la aplicación

### Desafío de visualización

Representar valores negativos en gráficos de barras puede resultar confuso visualmente, ya que intuitivamente asociamos barras más altas con valores "mejores" o "mayores". Sin embargo, en el caso de dBm, los valores menos negativos (más cercanos a 0) son los que representan señales más fuertes.

### Solución implementada

Para hacer la visualización más intuitiva:

1. **Transformación de valores**: 
   - Los valores de dBm se transforman a una escala positiva sumando 90
   - Esto convierte el rango típico de -90 a -30 dBm en un rango de 0 a 60
   - Resultado: las barras más altas representan señales más fuertes

2. **Etiquetas del eje Y**:
   - A pesar de la transformación interna, las etiquetas del eje Y muestran los valores reales de dBm
   - Se utiliza una función callback para convertir los valores transformados de vuelta a dBm en las etiquetas

3. **Tooltips informativos**:
   - Al pasar el cursor sobre las barras, se muestra el nombre de la red y su valor real de señal en dBm
   - Esto permite ver los valores exactos mientras se mantiene una visualización intuitiva

## Implementación técnica

La transformación se realiza en JavaScript, en las funciones `updateSignalChart` (dashboard) y `displayModalSignalChart` (historial):

```javascript
// Transformar los valores de dBm para que -90 sea 0 y -30 sea 60
for (let i = 0; i < networks.length; i++) {
    data[i] = networks[i].signal + 90;
}
```

La configuración de las escalas incluye:

```javascript
scales: {
    y: {
        title: {
            display: true,
            text: 'Intensidad de señal (dBm)'
        },
        min: 0,
        max: 60,
        ticks: {
            callback: function(value) {
                // Convertir el valor transformado de vuelta a dBm para las etiquetas
                return (value - 90) + ' dBm';
            }
        }
    }
}
```

## Beneficios

Esta implementación ofrece varios beneficios:

1. **Visualización intuitiva**: Las barras más altas representan claramente las señales más fuertes
2. **Precisión técnica**: Se mantienen los valores reales de dBm en las etiquetas y tooltips
3. **Experiencia de usuario mejorada**: Facilita la interpretación de los datos a simple vista

## Separación por bandas

Adicionalmente, los gráficos separan las redes por bandas:
- Azul: Redes en la banda de 2.4 GHz
- Rosa: Redes en la banda de 5 GHz

Esta separación por colores permite identificar rápidamente qué tipo de redes tienen mejor señal en cada ubicación.
