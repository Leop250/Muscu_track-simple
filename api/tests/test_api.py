import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

import pytest
from fastapi.testclient import TestClient

from main import Base, app, engine

SEANCE = {"exercice": "Développé couché", "series": 3, "repetitions": 10, "poids": 60, "jour": "2026-11-23"}


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_creer_puis_lister(client):
    reponse = client.post("/seances", json=SEANCE)
    assert reponse.status_code == 201
    assert reponse.json()["id"] == 1

    seances = client.get("/seances").json()
    assert len(seances) == 1
    assert seances[0]["exercice"] == "Développé couché"


def test_donnees_invalides_refusees(client):
    reponse = client.post("/seances", json={**SEANCE, "series": 0})
    assert reponse.status_code == 422


def test_supprimer(client):
    seance_id = client.post("/seances", json=SEANCE).json()["id"]
    assert client.delete(f"/seances/{seance_id}").status_code == 204
    assert client.get("/seances").json() == []
    assert client.delete(f"/seances/{seance_id}").status_code == 404
