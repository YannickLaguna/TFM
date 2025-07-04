#!/bin/bash

# Script de instalación y configuración automática para la aplicación de análisis financiero

# Crear directorio de logs
mkdir -p tests/logs
LOG_FILE="tests/logs/$(date '+%Y-%m-%d_%H-%M-%S')_instalacion.log"
echo "=== INSTALACIÓN DE LA APLICACIÓN DE ANÁLISIS FINANCIERO ===" > $LOG_FILE
echo "" >> $LOG_FILE

# 1. Crear entorno virtual
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Creando entorno virtual 'finpy'..." | tee -a $LOG_FILE
python -m venv finpy &>> $LOG_FILE

# 2. Conceder permisos de ejecución en PowerShell (solo relevante en Windows)
if [[ "$OS" == "Windows_NT" ]]; then
    echo "Concediendo permisos de ejecución en PowerShell..." | tee -a $LOG_FILE
    powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process" &>> $LOG_FILE
fi

# 3. Activar el entorno virtual
echo "Activando el entorno virtual..." | tee -a $LOG_FILE
echo "Intentando activar entorno virtual..." | tee -a $LOG_FILE
source finpy/Scripts/activate 2>> $LOG_FILE
ACTIVATION_STATUS=$?
echo "Código de salida de activación: $ACTIVATION_STATUS" | tee -a $LOG_FILE

# Verificar activación
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: El entorno virtual no se activó correctamente." | tee -a $LOG_FILE
    echo "Estado de VIRTUAL_ENV: $VIRTUAL_ENV" | tee -a $LOG_FILE
    echo "Ruta actual: $(pwd)" | tee -a $LOG_FILE
    echo "Contenido del directorio finpy:" | tee -a $LOG_FILE
    ls -la finpy 2>> $LOG_FILE | tee -a $LOG_FILE
    exit 1
fi

# 4. Instalar dependencias
echo "Instalando dependencias..." | tee -a $LOG_FILE
pip install --upgrade pip &>> $LOG_FILE
pip install -r requirements.txt &>> $LOG_FILE

# 5. Configurar la base de datos SQLite
echo "Inicializando la base de datos SQLite..." | tee -a $LOG_FILE
python -c "from app.DB.DataBase import initialize_database; initialize_database()" &>> $LOG_FILE

# 6. Iniciar la aplicación y mantenerla abierta
echo "Iniciando la aplicación..." | tee -a $LOG_FILE
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload | tee -a $LOG_FILE

# 6. Mensaje final
echo "Instalación y configuración completadas. Puedes iniciar la aplicación con:" | tee -a $LOG_FILE
echo "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" | tee -a $LOG_FILE
echo "La aplicación estará disponible en: http://localhost:8000" | tee -a $LOG_FILE

