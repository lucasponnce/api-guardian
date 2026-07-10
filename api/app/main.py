from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserCreate, UserOut
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models import User
from app.schemas.login import LoginRequest

app = FastAPI(title="API Guardian")

@app.get("/")
async def root():
    return {"message": "API Guardian corriendo"}

@app.get("/db-check")
async def db_check(db: Session = Depends(get_db)):
    return {"users_count": db.query(User).count()}

@app.post("/register", response_model=UserOut)
async def register(data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    new_user = User(username=data.username, password_hash=hash_password(data.password))

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    access_token = create_access_token({"sub": user.username})

    return {"acces_token": access_token, "token_type": "bearer"}