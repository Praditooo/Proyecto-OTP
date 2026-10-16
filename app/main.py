from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import models
from app.database import Base, engine
from app.limiter import limiter
from app.routes import auth, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de autenticación con OTP")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
def root():
    """Ruta de prueba para comprobar que la API está funcionando."""
    return {"mensaje": "API funcionando"}