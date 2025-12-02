from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session

from database import engine
import models
import schemas
from deps import get_db
from security import hash_password, verify_password, create_access_token
from auth_deps import get_current_user

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from uuid import uuid4

from ml import model_prediction
#create tables
models.Base.metadata.create_all(bind=engine)

#image directory local for now

UPLOAD_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

#health check initial
@app.get("/health")
def health():
    return {"status":"ok"}

#Endpoints

#Create User API
@app.post("/users/",response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    email_exists = db.query(models.User).filter(models.User.email == user_in.email).first()
    if email_exists:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Email Already Registered",
        )
    hashed_password = hash_password(user_in.password)
    db_user = models.User(
        name = user_in.name,
        email = user_in.email,
        hashed_password = hashed_password,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

#Get user details api
@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id:int, db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "User not found",
        )
    return user

#
@app.post("/login/", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Invalid email or password"
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid email or password"
        )
    
    access_token = create_access_token({"sub":str(user.id)})

    return {"access_token":access_token, "token_type":"bearer"}

@app.get("/me/", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user

#Prediction Endpoint API
@app.get("/predictions/me", response_model = list[schemas.PredictionOut])
def list_user_predictions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)):

    """Get current logged in user and show all the previoius predictions made for them"""

    preds = (
        db.query(models.Prediction)
        .filter(models.Prediction.user_id == current_user.id)
        .order_by(models.Prediction.created_at.desc())
        .all())
    return preds

@app.post("/predict/", response_model=schemas.PredictionOut)
async def predict(
        file: UploadFile = File(...),
        db:Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    """Predicts from uplaoded image file and updates predictions table. """

    #if file is not an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail= "File must be an image"
        )
    
    #saving image to local for now, change to s3 pending
    extension = os.path.splitext(file.filename)[1] or ".jpg"
    unique_name = f"{uuid4().hex}{extension}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    #running machine learning model 
    predicted_label, confidence = model_prediction(save_path)

    db_pred = models.Prediction(
        user_id = current_user.id,
        image_url = save_path,
        predicted_label = predicted_label,
        confidence = confidence,
        model_version = "resnet50_v1"
    )

    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)

    
    return db_pred