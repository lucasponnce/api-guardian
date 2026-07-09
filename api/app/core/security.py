from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Se usa en el registro
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Se usa en el login
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)