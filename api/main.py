import datetime as dt
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def database_url() -> str:
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    name = os.environ["POSTGRES_DB"]
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


engine = create_engine(database_url())
SessionLocal = sessionmaker(engine)


def get_db():
    with SessionLocal() as db:
        yield db


class Base(DeclarativeBase):
    pass


class Seance(Base):
    __tablename__ = "seances"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercice: Mapped[str] = mapped_column(String(100))
    series: Mapped[int]
    repetitions: Mapped[int]
    poids: Mapped[float]
    jour: Mapped[dt.date]


class SeanceIn(BaseModel):
    exercice: str = Field(min_length=1, max_length=100)
    series: int = Field(gt=0)
    repetitions: int = Field(gt=0)
    poids: float = Field(ge=0)
    jour: dt.date


class SeanceOut(SeanceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="MuscuTrack API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/seances", response_model=list[SeanceOut])
def lister_seances(db: Session = Depends(get_db)):
    return db.scalars(select(Seance).order_by(Seance.jour.desc(), Seance.id.desc())).all()


@app.post("/seances", response_model=SeanceOut, status_code=201)
def creer_seance(donnees: SeanceIn, db: Session = Depends(get_db)):
    seance = Seance(**donnees.model_dump())
    db.add(seance)
    db.commit()
    db.refresh(seance)
    return seance


@app.delete("/seances/{seance_id}", status_code=204)
def supprimer_seance(seance_id: int, db: Session = Depends(get_db)):
    seance = db.get(Seance, seance_id)
    if seance is None:
        raise HTTPException(status_code=404, detail="Séance introuvable")
    db.delete(seance)
    db.commit()
