import matplotlib
matplotlib.use("Agg")

import pandas as pd
import pytest


@pytest.fixture
def sample_fines():
    return pd.DataFrame({
        "CALIFICACION": ["  LEVE ", "GRAVE  ", " LEVE"],
        "DESCUENTO": [" SI ", "NO", " SI"],
        "HECHO-BOL": ["  A ", "B  ", " C"],
        "DENUNCIANTE": ["  POLICIA ", "AGENTE  ", " POLICIA"],
        "VEL_LIMITE": ["50", "50", "30"],
        "VEL_CIRCULA ": ["65", "not-a-number", "45"],
        "COORDENADA-X": ["440000.1", "440001.2", "bad-coordinate"],
        "COORDENADA-Y": ["4470000.1", "4470001.2", "4470002.3"],
        "ANIO": [2024, 2024, 2024],
        "MES": [9, 9, 10],
        "HORA": [14.30, 15.45, 10.15],
        "IMP_BOL": [100.0, 200.0, 80.0],
    })
