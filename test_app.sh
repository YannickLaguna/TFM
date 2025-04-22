#!/bin/bash

# Script para probar la aplicación de análisis financiero -- IGNORAR

# Crear directorio para pruebas
mkdir -p test_results

echo "=== PRUEBAS DE LA APLICACIÓN DE ANÁLISIS FINANCIERO ==="
echo "Fecha: $(date)"
echo ""

# Activar entorno virtual
cd /home/ubuntu/finapp
source venv/bin/activate

echo "=== 1. Prueba de descarga de datos ==="
python3 src/app.py descargar AAPL MSFT GOOGL --periodo 3mo
echo ""

echo "=== 2. Prueba de análisis de activo ==="
python3 src/app.py analizar AAPL --periodo 3mo
echo ""

echo "=== 3. Prueba de análisis de correlación ==="
python3 src/app.py correlacion AAPL MSFT GOOGL --periodo 3mo
echo ""

echo "=== 4. Prueba de creación de estrategia ==="
python3 src/app.py estrategia "Cruce de Medias" cruce_medias --descripcion "Estrategia basada en cruce de medias móviles" --parametros '{"periodo_rapido": 20, "periodo_lento": 50}'
echo ""

echo "=== 5. Prueba de backtesting ==="
# Asumimos que la estrategia creada tiene ID 1
python3 src/app.py backtest 1 AAPL --periodo 3mo
echo ""

echo "=== 6. Prueba de optimización de estrategia ==="
python3 src/app.py optimizar cruce_medias AAPL --periodo 3mo --metrica ratio_sharpe
echo ""

echo "=== 7. Prueba de generación de reporte ==="
python3 src/app.py reporte AAPL --periodo 3mo
echo ""

echo "=== PRUEBAS COMPLETADAS ==="
echo "Los resultados se pueden encontrar en los directorios data/graficos y data/reportes"
