# Start Generation Here
FROM python:3.9

# Establecer el directorio de trabajo
WORKDIR /code

# Copiar los archivos necesarios
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para ejecutar el script principal
CMD ["python", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
# End Generation Here
