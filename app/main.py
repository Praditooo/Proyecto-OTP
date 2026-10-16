from fastapi import FastAPI

from app import models
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de autenticación con OTP")


@app.get("/")
def root():
    """Ruta de prueba para comprobar que la API está funcionando."""
    return {"mensaje": "API funcionando"}