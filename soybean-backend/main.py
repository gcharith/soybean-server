from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from database import engine
import models
import schemas
from deps import get_db
from security import hash_password, verify_password, create_access_token
from auth_deps import get_current_user

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()

from ml import model_prediction
from storage import upload_image_to_s3

#create tables
models.Base.metadata.create_all(bind=engine)

#image directory local for now

UPLOAD_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)
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
    
    file_bytes = await file.read()

    #saving image to local for now, change to s3 pending
    extension = os.path.splitext(file.filename)[1] or ".jpg"
    
    #running machine learning model 
    predicted_label, confidence = model_prediction(file_bytes)

    #getting s3 url 
    s3_url = upload_image_to_s3(
        file_bytes=file_bytes,
        predicted_class=predicted_label,
        extension=extension,
        content_type=file.content_type
    )

    #saving prediction to databaseßßß
    db_pred = models.Prediction(
        user_id = current_user.id,
        image_url = s3_url,
        predicted_label = predicted_label,
        confidence = confidence,
        model_version = "resnet50_v1"
    )

    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)

    
    return db_pred


# --FEEDBACK ENDPOINTS--

@app.post("/feedback/", response_model = schemas.FeedbackOut)
def create_feedback(
    feedback_in: schemas.FeedbackCreate,
    db:Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Accepts user feedback for a prediction and puts it inside a feedback table"""

    pred = db.query(models.Prediction).filter(models.Prediction.id == feedback_in.prediction_id).first()
    if pred is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "Prediction does not exist"
        )
    if pred.user_id != current_user.id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail="You can give  feedback to your predictions only."
        )
    
    db_fb = models.Feedback(
        user_id = current_user.id,
        prediction_id = pred.id,
        rating = feedback_in.rating,
        is_correct = feedback_in.is_correct,
        comment = feedback_in.comment,
    )

    db.add(db_fb)
    db.commit()
    db.refresh(db_fb)

    return db_fb

@app.get("/feedback/me", response_model = list[schemas.FeedbackOut])
def list_feedback(
    db:Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Returns all the feedbacks submitted by a user"""
    fb_list = (
        db.query(models.Feedback)
        .filter(models.Feedback.user_id == current_user.id)
        .order_by(models.Feedback.created_at.desc())
        .all()
    )

    return fb_list