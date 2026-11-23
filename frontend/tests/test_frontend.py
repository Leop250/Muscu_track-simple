import json

import httpx
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def fausse_api(monkeypatch):
    seances = []

    def repondre(requete: httpx.Request):
        if requete.method == "GET":
            return httpx.Response(200, json=seances)
        if requete.method == "POST":
            seance = {"id": len(seances) + 1, **json.loads(requete.content)}
            seances.append(seance)
            return httpx.Response(201, json=seance)
        if requete.method == "DELETE":
            seance_id = int(requete.url.path.rsplit("/", 1)[1])
            seances[:] = [s for s in seances if s["id"] != seance_id]
            return httpx.Response(204)

    monkeypatch.setattr(main, "api", httpx.Client(base_url="http://api", transport=httpx.MockTransport(repondre)))
    return seances


@pytest.fixture
def client():
    return TestClient(main.app)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_page_vide(client, fausse_api):
    reponse = client.get("/")
    assert reponse.status_code == 200
    assert "Aucune séance" in reponse.text


def test_ajouter_puis_supprimer(client, fausse_api):
    formulaire = {"exercice": "Squat", "series": 3, "repetitions": 10, "poids": 80, "jour": "2026-11-23"}
    client.post("/ajouter", data=formulaire)
    assert "Squat" in client.get("/").text

    client.post("/supprimer/1")
    assert "Aucune séance" in client.get("/").text


def test_api_injoignable(client, monkeypatch):
    def panne(requete):
        raise httpx.ConnectError("injoignable")

    monkeypatch.setattr(main, "api", httpx.Client(base_url="http://api", transport=httpx.MockTransport(panne)))
    assert "injoignable" in client.get("/").text
