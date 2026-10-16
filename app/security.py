import bcrypt


def hash_password(password: str) -> str:
    """Convierte la contraseña en un hash bcrypt (la "sal" aleatoria va incluida)."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano contra el hash guardado."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))