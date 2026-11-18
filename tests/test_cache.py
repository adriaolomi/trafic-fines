import os
import time
import tempfile
from pathlib import Path

import pytest

import trafic_fines.cache as cache_module
from trafic_fines.cache import Cache, CacheError, CacheURL


@pytest.fixture
def cache(monkeypatch):
    cache_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(cache_module, "CACHE_DIR", cache_dir)
    return Cache(app_name="pytest_cache", obsolescence=2)


@pytest.fixture
def cache_url(monkeypatch):
    cache_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(cache_module, "CACHE_DIR", cache_dir)
    return CacheURL(app_name="pytest_cache_url", obsolescence=2)


def test_cache_properties(cache):
    assert cache.app_name == "pytest_cache"
    assert cache.cache_dir.name == "pytest_cache"
    assert cache.obsolescence == 2


def test_set_exists_and_load(cache):
    cache.set("sample.txt", "hello pytest")
    assert cache.exists("sample.txt") is True
    assert cache.load("sample.txt") == "hello pytest"


def test_exists_returns_false_for_missing_file(cache):
    assert cache.exists("missing.txt") is False


def test_load_missing_file_raises_cache_error(cache):
    with pytest.raises(CacheError):
        cache.load("missing.txt")


def test_how_old_returns_age_in_milliseconds(cache):
    cache.set("old.txt", "data")
    file_path = cache.cache_dir / "old.txt"
    old_timestamp = time.time() - 10
    os.utime(file_path, (old_timestamp, old_timestamp))

    age_ms = cache.how_old("old.txt")
    assert 9000 <= age_ms <= 12000


def test_delete_removes_file(cache):
    cache.set("sample.txt", "data")
    cache.delete("sample.txt")
    assert cache.exists("sample.txt") is False


def test_clear_removes_cache_directory(cache):
    cache.set("one.txt", "1")
    cache.set("two.txt", "2")
    cache.clear()
    assert cache.cache_dir.exists() is False


def test_cacheurl_downloads_and_caches_response(cache_url, monkeypatch):
    class MockResponse:
        status_code = 200
        text = "remote content"

    calls = []

    def mock_get(url):
        calls.append(url)
        return MockResponse()

    monkeypatch.setattr(cache_module.requests, "get", mock_get)

    first = cache_url.get("https://example.test/data.csv")
    second = cache_url.get("https://example.test/data.csv")

    assert first == "remote content"
    assert second == "remote content"
    assert calls == ["https://example.test/data.csv"]


def test_cacheurl_connection_error_returns_none(cache_url, monkeypatch):
    import requests

    def mock_get(url):
        raise requests.RequestException("network unavailable")

    monkeypatch.setattr(cache_module.requests, "get", mock_get)
    assert cache_url.get("https://example.test/data.csv") is None


def test_cacheurl_load_missing_url_raises_cache_error(cache_url):
    with pytest.raises(CacheError):
        cache_url.load("https://example.test/missing.csv")
