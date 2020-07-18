import pytest

from yap import create_app


def test_create_app_requires_proper_secret_key():
    with pytest.raises(RuntimeError) as e:
        create_app()
    assert "SECRET_KEY" in str(e.value)


def test_create_app_allows_default_secret_key_in_dev_mode(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")

    assert create_app().debug


def test_create_app_allows_default_secret_key_in_test_mode():
    assert create_app({"TESTING": True}).testing
