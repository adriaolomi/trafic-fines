# Tests de `trafic_fines`

Instala pytest desde la raíz del proyecto:

```bash
uv add --dev pytest
```

Ejecuta todos los tests:

```bash
uv run python -m pytest --doctest-modules --cov=. --cov-report=html
```

Ejecuta un archivo concreto:

```bash
uv run pytest tests/test_cache.py -v
uv run pytest tests/test_madridFines.py -v
```

Los tests no descargan datos reales. Las peticiones HTTP y las cargas de datasets se simulan mediante `monkeypatch`, y la caché se redirige a directorios temporales.