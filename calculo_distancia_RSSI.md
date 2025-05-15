jlvillaronga@teccam.net De:

Lucas Lopez <lucasl@teccam.net> Enviado el:

jueves, 15 de mayo de 2025 10:59

Para:

José Luis Vil aronga; Gustavo Donandueno; gdonan@hotmail.com; Pedro Franco Asunto:

calculo aproximado de distancia al router wifi El cálculo de distancia a partir de la señal WiFi \(RSSI\) es una estimación empírica, ya que no hay un método directo ni exacto sin hardware especializado. Se basa en el modelo de pérdida de propagación logarítmica, que relaciona la pérdida de potencia con la distancia. 

Fórmula general: 

d=10\(\(TxPower−RSSI\)/\(10∗n\)\)d = 10 ^ \(\(TxPower - RSSI\) / \(10 \* n\)\) d=10\(\(TxPower−RSSI\)/\(10∗n\)\) Donde: 

 d = distancia estimada en metros 

 TxPower = potencia de transmisión del router o punto de acceso a 1 metro \(en dBm\). 

o Típicamente entre -30 dBm y -50 dBm 

 RSSI = intensidad de señal recibida \(en dBm\), medida por el ESP32/ESP8266 

 n = factor de propagación \(path-loss exponent\) o 2 en espacio libre 

o 2.7 a 4 en interiores \(paredes, interferencias\) Ejemplo práctico: 

Supongamos: 

 TxPower = -40 dBm \(valor aproximado típico de un router a 1 metro\) 

 RSSI = -70 dBm 

 n = 2.5 \(ambiente con obstáculos\) Entonces: 

d=10\(\(−40−\(−70\)\)/\(10∗2.5\)\)=10\(30/25\)=101.2≈15.8metrosd = 10 ^ \(\(-40 - \(-70\)\) / \(10 \* 2.5\)\) = 10 ^ \(30 / 

25\) = 10 ^ 1.2 ≈ 15.8 metros d=10\(\(−40−\(−70\)\)/\(10∗2.5\)\)=10\(30/25\)=101.2≈15.8metros 1
