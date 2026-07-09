from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User

app = FastAPI(title="API Guardian")

@app.get("/")
async def root():
    return {"message": "API Guardian corriendo"}

@app.get("/db-check")
async def db_check(db: Session = Depends(get_db)):
    return {"users_count": db.query(User).count()}