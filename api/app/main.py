from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserCreate, UserOut
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token, get_current_user
from app.models import User
from fastapi.security import OAuth2PasswordRequestForm

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
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    access_token = create_access_token({"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
