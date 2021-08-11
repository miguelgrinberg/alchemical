import pytest
from flaskr import create_app


def test_config():
    """Test create_app without passing test config."""
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_db_url_environ(monkeypatch):
    """Test DATABASE_URL environment variable."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///environ")
    app = create_app()
    assert app.config["ALCHEMICAL_DATABASE_URL"] == "sqlite:///environ"


@pytest.mark.asyncio
async def test_init_db_command(runner, monkeypatch):
    class Recorder:
        called = False

    async def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr("flaskr.init_db", fake_init_db)
    result = await runner.invoke(args=["init-db"])
    assert "Initialized" in result.output
    assert Recorder.called
