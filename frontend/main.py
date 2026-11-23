import datetime as dt
import os

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

API_URL = os.environ.get("API_URL", "http://api:8000")

app = FastAPI(title="MuscuTrack Frontend")
templates = Jinja2Templates(directory="templates")
api = httpx.Client(base_url=API_URL, timeout=5)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def accueil(request: Request):
    seances, erreur = [], None
    try:
        reponse = api.get("/seances")
        reponse.raise_for_status()
        seances = reponse.json()
    except httpx.HTTPError:
        erreur = "L'API est injoignable pour le moment."
    return templates.TemplateResponse(
        request,
        "index.html",
        {"seances": seances, "erreur": erreur, "aujourdhui": dt.date.today().isoformat()},
    )


@app.post("/ajouter")
def ajouter(
    exercice: str = Form(),
    series: int = Form(),
    repetitions: int = Form(),
    poids: float = Form(),
    jour: str = Form(),
):
    api.post(
        "/seances",
        json={"exercice": exercice, "series": series, "repetitions": repetitions, "poids": poids, "jour": jour},
    )
    return RedirectResponse("/", status_code=303)


@app.post("/supprimer/{seance_id}")
def supprimer(seance_id: int):
    api.delete(f"/seances/{seance_id}")
    return RedirectResponse("/", status_code=303)
