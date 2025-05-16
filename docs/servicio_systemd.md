# Servicio Systemd para WiFi Analyzer

Este documento explica cómo se ha configurado el servicio systemd para la aplicación WiFi Analyzer y cómo gestionarlo.

## Configuración del servicio

La aplicación WiFi Analyzer se ejecuta como un servicio systemd, lo que permite:
- Iniciar automáticamente al arrancar el sistema
- Reiniciar automáticamente en caso de fallo
- Gestión centralizada mediante systemctl

El archivo de configuración del servicio se encuentra en `/etc/systemd/system/wifi-analyzer.service` con el siguiente contenido:

```ini
[Unit]
Description=WiFi Analyzer Service
After=network.target mongodb.service
Wants=mongodb.service

[Service]
User=pi
WorkingDirectory=/home/pi/wifi-test
ExecStart=/home/pi/wifi-test/venv/bin/python /home/pi/wifi-test/app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## Gestión del servicio

### Usando el script de gestión

Se proporciona un script `manage-service.sh` para facilitar la gestión del servicio:

```bash
# Iniciar el servicio
./manage-service.sh start

# Detener el servicio
./manage-service.sh stop

# Reiniciar el servicio
./manage-service.sh restart

# Ver el estado del servicio
./manage-service.sh status

# Ver los logs del servicio
./manage-service.sh logs
```

### Usando systemctl directamente

También se puede gestionar el servicio directamente con systemctl:

```bash
# Iniciar el servicio
sudo systemctl start wifi-analyzer.service

# Detener el servicio
sudo systemctl stop wifi-analyzer.service

# Reiniciar el servicio
sudo systemctl restart wifi-analyzer.service

# Ver el estado del servicio
sudo systemctl status wifi-analyzer.service

# Ver los logs del servicio
sudo journalctl -u wifi-analyzer.service -f

# Habilitar el inicio automático
sudo systemctl enable wifi-analyzer.service

# Deshabilitar el inicio automático
sudo systemctl disable wifi-analyzer.service
```

## Acceso a la aplicación

Una vez que el servicio está en ejecución, la aplicación WiFi Analyzer está disponible en:

- URL local: http://localhost:8000
- URL en la red: http://<IP-del-Raspberry-Pi>:8000

## Solución de problemas

Si el servicio no se inicia correctamente:

1. Verificar el estado del servicio:
   ```bash
   sudo systemctl status wifi-analyzer.service
   ```

2. Revisar los logs para ver errores detallados:
   ```bash
   sudo journalctl -u wifi-analyzer.service -e
   ```

3. Asegurarse de que MongoDB esté funcionando:
   ```bash
   sudo systemctl status mongodb
   ```

4. Verificar los permisos:
   ```bash
   ls -la /home/pi/wifi-test
   ls -la /home/pi/wifi-test/venv/bin/python
   ```

## Actualización de la aplicación

Después de actualizar el código de la aplicación, reinicie el servicio para aplicar los cambios:

```bash
sudo systemctl restart wifi-analyzer.service
```
