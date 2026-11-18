import pandas as pd
import pytest

import trafic_fines.madridFines as madrid_module
from trafic_fines.madridFines import MadridError, MadridFines


def test_clean_returns_none(sample_fines):
    result = MadridFines.clean(sample_fines)
    assert result is None


def test_clean_modifies_dataframe(sample_fines):
    original = sample_fines
    MadridFines.clean(sample_fines)
    assert sample_fines is original
    assert isinstance(sample_fines.index, pd.DatetimeIndex)


def test_clean_creates_datetime_index(sample_fines):
    MadridFines.clean(sample_fines)
    assert sample_fines.index[0] == pd.Timestamp("2024-09-01 14:30:00")
    assert sample_fines.index[1] == pd.Timestamp("2024-09-01 15:45:00")
    assert sample_fines.index[2] == pd.Timestamp("2024-10-01 10:15:00")


def test_clean_removes_spaces_from_text(sample_fines):
    MadridFines.clean(sample_fines)
    assert sample_fines["CALIFICACION"].tolist() == ["LEVE", "GRAVE", "LEVE"]
    assert sample_fines["DESCUENTO"].tolist() == ["SI", "NO", "SI"]
    assert sample_fines["HECHO-BOL"].tolist() == ["A", "B", "C"]
    assert sample_fines["DENUNCIANTE"].tolist() == ["POLICIA", "AGENTE", "POLICIA"]


@pytest.mark.parametrize(
    "column, expected_type",
    [
        ("VEL_LIMITE", "numeric"),
        ("VEL_CIRCULA", "numeric"),
        ("COORDENADA-X", "numeric"),
        ("COORDENADA-Y", "numeric"),
    ],
)
def test_clean_converts_numeric_columns(sample_fines, column, expected_type):
    MadridFines.clean(sample_fines)
    assert pd.api.types.is_numeric_dtype(sample_fines[column])


def test_clean_converts_invalid_numeric_values_to_nan(sample_fines):
    MadridFines.clean(sample_fines)
    assert pd.isna(sample_fines["VEL_CIRCULA"].iloc[1])
    assert pd.isna(sample_fines["COORDENADA-X"].iloc[2])


def test_clean_removes_null_character_from_column_names(sample_fines):
    sample_fines["EXTRA\x00"] = ["a", "b", "c"]
    MadridFines.clean(sample_fines)
    assert "EXTRA" in sample_fines.columns


def test_get_url_finds_detail_resource(monkeypatch):
    html = """
    <div class="tracked-resource-item" data-key="2024-Septiembre">
        <a title="Detalle. Multas de circulación">Detalle</a>
        <a class="resource-url-analytics" href="dataset/fines.csv">CSV</a>
    </div>
    """

    class MockResponse:
        status_code = 200
        text = html

    def mock_get(url):
        return MockResponse()

    monkeypatch.setattr(madrid_module.requests, "get", mock_get)
    result = madrid_module.get_url(2024, 9)
    assert result == madrid_module.RAIZ + "dataset/fines.csv"


def test_get_url_request_error_raises_madrid_error(monkeypatch):
    class MockResponse:
        status_code = 500
        text = ""

    def mock_get(url):
        return MockResponse()

    monkeypatch.setattr(madrid_module.requests, "get", mock_get)
    with pytest.raises(MadridError):
        madrid_module.get_url(2024, 9)


def test_load_reads_csv_from_cache(monkeypatch):
    expected_url = "https://example.test/fines.csv"
    csv_content = (
        "CALIFICACION;DESCUENTO;ANIO;MES;HORA\n"
        "LEVE;SI;2024;9;14.30\n"
    )

    def mock_get_url(year, month):
        return expected_url

    class MockCache:
        def get(self, url):
            assert url == expected_url
            return csv_content

    monkeypatch.setattr(madrid_module, "get_url", mock_get_url)
    result = MadridFines.load(2024, 9, MockCache())

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert result.loc[0, "CALIFICACION"] == "LEVE"
    assert result.loc[0, "MES"] == 9


def test_add_loads_cleans_and_appends_dataset(sample_fines, monkeypatch):
    madrid = MadridFines(app_name="pytest_madrid", obsolescence=2)

    def mock_load(year, month, cacheurl):
        return sample_fines.copy()

    monkeypatch.setattr(MadridFines, "load", staticmethod(mock_load))
    madrid.add(year=2024, month=9)

    assert len(madrid.data) == 3
    assert isinstance(madrid.data.index, pd.DatetimeIndex)
    assert (9, 2024) in madrid.loaded


def test_add_does_not_load_same_month_twice(sample_fines, monkeypatch):
    madrid = MadridFines(app_name="pytest_duplicate", obsolescence=2)
    calls = []

    def mock_load(year, month, cacheurl):
        calls.append((year, month))
        return sample_fines.copy()

    monkeypatch.setattr(MadridFines, "load", staticmethod(mock_load))
    madrid.add(year=2024, month=9)
    madrid.add(year=2024, month=9)

    assert calls == [(2024, 9)]
    assert len(madrid.data) == 3
    assert madrid.loaded == [(9, 2024)]


def test_fines_calification_counts_by_month_and_year(sample_fines):
    madrid = MadridFines(app_name="pytest_calification", obsolescence=2)
    MadridFines.clean(sample_fines)
    madrid.data = sample_fines

    result = madrid.fines_calification()

    assert result.loc[(9, 2024), "LEVE"] == 1
    assert result.loc[(9, 2024), "GRAVE"] == 1
    assert result.loc[(10, 2024), "LEVE"] == 1


def test_total_payment_calculates_minimum_and_maximum(sample_fines):
    madrid = MadridFines(app_name="pytest_payment", obsolescence=2)
    MadridFines.clean(sample_fines)
    madrid.data = sample_fines

    result = madrid.total_payment()

    assert result.loc[(9, 2024), "PRECIO_MAX"] == 300.0
    assert result.loc[(9, 2024), "PRECIO_MIN"] == 250.0
    assert result.loc[(10, 2024), "PRECIO_MAX"] == 80.0
    assert result.loc[(10, 2024), "PRECIO_MIN"] == 40.0


def test_fines_hour_creates_image_file(sample_fines, monkeypatch):
    from pathlib import Path
    import tempfile

    madrid = MadridFines(app_name="pytest_plot", obsolescence=2)
    MadridFines.clean(sample_fines)
    madrid.data = sample_fines

    output_dir = Path(tempfile.mkdtemp())
    output = output_dir / "fines_by_hour.png"
    madrid.fines_hour(fig_name=str(output))

    assert output.exists()
    assert output.stat().st_size > 0


def test_clean_cache_calls_cache_clear(monkeypatch):
    madrid = MadridFines(app_name="pytest_clear", obsolescence=2)
    calls = []

    def mock_clear():
        calls.append(True)

    monkeypatch.setattr(madrid.cacheurl, "clear", mock_clear)
    madrid.clean_cache()
    assert calls == [True]


def test_madridfines_str():
    madrid = MadridFines(app_name="pytest_madrid", obsolescence=2)

    result = str(madrid)

    assert isinstance(result, str)
    assert "Data:" in result
    assert "Loaded:" in result
    assert str(madrid.data) in result
    assert str(madrid.loaded) in result


def test_loaded_setter():
    madrid = MadridFines(app_name="pytest_madrid", obsolescence=2)

    loaded = [(9, 2024), (10, 2024)]

    madrid.loaded = loaded

    assert madrid.loaded == loaded
    assert madrid.loaded is loaded
