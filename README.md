TODO subir a github, eliminando el venv y asegurarme de que al profe le funcione
TODO conseguir que la DB sea completamente funcional, que funcione la descarga de distintos tickers, que se puedan eliminar los datos y que se puedan visualizar
# Financial Data Analysis Application

Una aplicación web para análisis de datos financieros, backtesting de estrategias y visualización de indicadores técnicos.

## Descripción

Esta aplicación permite a los usuarios:

- Obtener y visualizar datos históricos de precios de diferentes activos financieros
- Realizar análisis técnico con varios indicadores (medias móviles, RSI, MACD, Bandas de Bollinger)
- Crear y probar estrategias de trading personalizadas
- Optimizar los parámetros de las estrategias para mejorar el rendimiento
- Generar informes completos para ayudar en la toma de decisiones

## Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Docker y Docker Compose (opcional, para instalación con Docker)
- Git (opcional, para clonar el repositorio)

## Instalación

### Opción 1: Instalación con Docker

1. Clona el repositorio o descarga los archivos del proyecto:
   \`\`\`bash
   git clone <url-del-repositorio>
   cd <nombre-del-directorio>
   \`\`\`

2. Construye y ejecuta los contenedores con Docker Compose:
   \`\`\`bash
   docker-compose up -d
   \`\`\`

3. La aplicación estará disponible en: http://localhost:8000

4. Para detener los contenedores:
   \`\`\`bash
   docker-compose down
   \`\`\`

### Opción 2: Instalación con entorno virtual (venv)

1. Clona el repositorio o descarga los archivos del proyecto:
   \`\`\`bash
   git clone <url-del-repositorio>
   cd <nombre-del-directorio>
   \`\`\`

2. Crea un entorno virtual:
   \`\`\`bash
   python -m venv finpy
   \`\`\`

3. Activa el entorno virtual:
   - En Windows:
     \`\`\`bash
     finpy\Scripts\activate
     \`\`\`
   - En macOS/Linux:
     \`\`\`bash
     source finpy/bin/activate
     \`\`\`

4. Instala las dependencias:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

5. Configura la base de datos SQLite:
   \`\`\`bash
   python -c "from app.DB.DataBase import initialize_database; initialize_database()"
   \`\`\`

6. Ejecuta la aplicación:
   \`\`\`bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   \`\`\`

7. La aplicación estará disponible en: http://localhost:8000

## Estructura del proyecto

\`\`\`
.
├── app/
│   ├── DB/
│   │   └── DataBase.py       # Configuración y conexión a la base de datos
│   ├── static/               # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/            # Plantillas HTML
│   ├── analysis.py           # Funciones de análisis de datos
│   ├── backtest.py           # Funciones para backtesting de estrategias
│   ├── data_fetcher.py       # Funciones para obtener datos financieros
│   ├── indicators.py         # Funciones para calcular indicadores técnicos
│   ├── main.py               # Punto de entrada de la aplicación FastAPI
│   ├── models.py             # Modelos de datos
│   └── routes.py             # Rutas de la API
├── data/
│   ├── graficos/             # Gráficos generados
│   └── reportes/             # Informes generados
├── docker-compose.yml        # Configuración de Docker Compose
├── Dockerfile                # Configuración de Docker
├── requirements.txt          # Dependencias del proyecto
└── README.md                 # Este archivo
\`\`\`

## Uso de la aplicación

### Página principal

La página principal muestra un resumen de la aplicación y enlaces a las diferentes secciones.

### Dashboard

El dashboard proporciona una visión general de los activos disponibles y sus datos más recientes.

### Gestión de datos

En esta sección puedes:
- Obtener datos históricos de nuevos activos
- Ver los activos disponibles en la base de datos
- Actualizar datos existentes

Para obtener datos de un nuevo activo:
1. Introduce el símbolo del activo (por ejemplo, AAPL para Apple)
2. Selecciona el período de tiempo
3. Haz clic en "Obtener datos"

### Análisis

En esta sección puedes:
- Analizar un activo individual
- Realizar análisis de correlación entre múltiples activos

Para analizar un activo:
1. Selecciona el activo de la lista desplegable
2. Selecciona el período de tiempo
3. Haz clic en "Analizar"

Para analizar correlaciones:
1. Introduce los símbolos de los activos separados por comas
2. Selecciona el período de tiempo
3. Haz clic en "Analizar correlación"

### Indicadores técnicos

En esta sección puedes generar y visualizar diferentes indicadores técnicos:
- Media móvil simple (SMA)
- Media móvil exponencial (EMA)
- Índice de fuerza relativa (RSI)
- Bandas de Bollinger
- MACD (Convergencia/Divergencia de Medias Móviles)

Para generar un indicador:
1. Selecciona el activo
2. Selecciona el indicador
3. Configura los parámetros del indicador
4. Haz clic en "Generar"

### Estrategias

En esta sección puedes:
- Crear nuevas estrategias de trading
- Probar estrategias existentes
- Optimizar los parámetros de las estrategias

Para crear una estrategia:
1. Introduce un nombre y descripción
2. Escribe el código de la estrategia en Python
3. Define los parámetros
4. Haz clic en "Crear estrategia"

Para probar una estrategia:
1. Selecciona la estrategia
2. Selecciona el activo
3. Configura los parámetros del backtest
4. Haz clic en "Ejecutar backtest"

### Informes

En esta sección puedes generar informes completos sobre activos financieros, incluyendo:
- Análisis de mercado
- Indicadores técnicos
- Resultados de backtesting de estrategias

Para generar un informe:
1. Selecciona el activo
2. Selecciona el período de tiempo
3. Haz clic en "Generar informe"

## Solución de problemas comunes

### Error al obtener datos de un activo

- Verifica que el símbolo del activo sea correcto
- Comprueba tu conexión a Internet
- Asegúrate de que el activo esté disponible en Yahoo Finance

### Error al ejecutar un backtest

- Verifica que el código de la estrategia no contenga errores
- Asegúrate de que los parámetros estén dentro de los rangos válidos
- Comprueba que haya suficientes datos históricos para el período seleccionado

### La aplicación no se inicia

Con Docker:
- Verifica que Docker y Docker Compose estén instalados y funcionando
- Comprueba los logs con `docker-compose logs`

Con venv:
- Asegúrate de que el entorno virtual esté activado
- Verifica que todas las dependencias estén instaladas
- Comprueba que el puerto 8000 no esté siendo utilizado por otra aplicación

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir los cambios que te gustaría hacer.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.
