from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.routes import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de autenticación con OTP")

app.include_router(auth.router)


@app.get("/")
def root():
    """Ruta de prueba para comprobar que la API está funcionando."""
    return {"mensaje": "API funcionando"}