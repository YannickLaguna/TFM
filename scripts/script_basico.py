"""
Este script básico inicia una aplicación de análisis de datos financieros usando FastAPI.
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    """
    Punto de entrada principal de la aplicación.
    """
    return {"mensaje": "Bienvenido a la aplicación de análisis de datos financieros."}

if __name__ == '__main__':
    # Inicia el servidor de FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)


