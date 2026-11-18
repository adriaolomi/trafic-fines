# Trafic-Fines

Paquete de Python para la descarga, almacenamiento, procesamiento y análisis de datos de multas de circulación del Ayuntamiento de Madrid, publicados a través del portal de datos abiertos **datos.madrid.es**.

## Nota sobre el uso de inteligencia artificial: 
Para el desarrollo de este proyecto se ha utilizado ChatGPT como herramienta de apoyo en la redacción de este README, la elaboración de los docstrings y el planteamiento de los tests. La lógica y la implementación del programa han sido desarrolladas por mí. Puntualmente, también se ha consultado la IA para resolver dudas concretas sobre atributos y llamadas a determinados métodos.

## Funcionalidades

El paquete se divide en dos módulos principales:

### 1. `cache.py`
Implementa un sistema de caché para almacenar información localmente y evitar descargas innecesarias.

Incluye:
- `Cache`: gestión de archivos almacenados en caché.
- `CacheURL`: descarga y almacenamiento de contenido procedente de URLs.
- Comprobación de existencia, antigüedad y eliminación de elementos.
- Gestión de errores mediante `CacheError`.

### 2. `madridFines.py`
Permite trabajar con los datos de multas de circulación de Madrid.

Incluye:
- Descarga y carga de los ficheros mensuales.
- Limpieza y transformación de los datos.
- Integración con el sistema de caché.
- Análisis y visualización de las multas, incluyendo:
  - Distribución por calificación.
  - Importe total de las multas.
  - Distribución de multas por hora.

## Instalación

Clona el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd trafic-fines
```

Instala el módulo:

```bash
uv build
```

## Uso básico

Ejemplo de importación de los módulos:

```python
from trafic_fines.cache import Cache, CacheURL
from trafic_fines.madridFines import MadridFines

# Crear un sistema de caché para URLs
cache = CacheURL("madrid_fines", 12)

# Inicializar el conjunto de datos
fines = MadridFines(cacheurl=cache)

# Cargar los datos
fines.add(year=2025, month=9)
fines.add(year=2025, month=10)

# Consultar y analizar los datos
fines.fines_calification()
fines.total_payment()
fines.fines_hour("test.png")
```

## Estructura del proyecto

```text
trafic-fines/
├── src/
│   └── trafic_fines/
│       ├── __init__.py
│       ├── cache.py
│       └── madridFines.py
├── tests/
│   ├── test_cache.py
│   └── test_madridFines.py
├── notebooks/
├── pyproject.toml
└── README.md
```

## Tests

Para ejecutar las tests y sacar un informe HTML:

```bash
uv run python -m pytest --doctest-modules --cov=. --cov-report=html
```

Para hacer la comprobación de tipos con uv:
```bash
uv run mypy src/
```
