from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
import os, re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Se usa en el registro
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Se usa en el login
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Función para crear el token
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Función para decodificar el token
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        return sub
    except jwt.JWTError:
        return None
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="El token es inválido o ha expirado")

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise HTTPException(status_code=401, detail="El usuario no existe")
    
    return user

def redact_sensitive_fields(text):
    if text is None:
        return None
    
    text = re.sub(r'"password"\s*:\s*"[^"]*"', '"password": "***"', text)
    text = re.sub(r'password=[^&]*', 'password=***', text)
    return text