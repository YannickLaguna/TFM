"""
Este script básico inicia una aplicación de análisis de datos financieros usando FastAPI.
POR AHORA: ejecuta main.py y ya está
"""
import uvicorn
import os
import sys

def main():
    """
    Función principal que inicia la aplicación en modo desarrollo.
    Configura el servidor uvicorn con recarga automática.
    """
    # Asegurarse de que el directorio raíz del proyecto esté en el path de Python
    # Esto permite importar módulos como 'app.main' correctamente.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_dir = os.path.join(current_dir, '..') # Sube un nivel desde 'scripts'
    sys.path.insert(0, project_root_dir) # Añade la raíz al inicio del sys.path
    
    # Configurar y ejecutar el servidor
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Activa la recarga automática en desarrollo
        log_level="info"
    )

if __name__ == "__main__":
    main()
