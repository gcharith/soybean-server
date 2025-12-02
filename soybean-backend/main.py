from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import engine
import models
import schemas
from deps import get_db

#create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health():
    return {"status":"ok"}

#Endpoints

@app.post("/users/",response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    email_exists = db.query(models.User).filter(models.User.email == user_in.email).first()
    if email_exists:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Email Already Registered",
        )
    
    db_user = models.User(
        name = user_in.name,
        email = user_in.email,
        hashed_password = user_in.password,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id:int, db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "User not found",
        )
    return user