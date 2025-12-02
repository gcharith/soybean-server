from pydantic import BaseModel
from datetime import datetime
from typing import Optional

##USER
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password:str

class UserOut(UserBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True



##PREDICTION
class PredictionBase(BaseModel):
    image_url: str
    predicted_label:str
    confidence: Optional[float] = None
    model_version: Optional[str] = None

class PredictionCreate(PredictionBase):
    pass 

class PredictionOut(PredictionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

##FEEDBACK
class FeedbackBase(BaseModel):
    prediction_id: int
    rating: Optional[int] = None
    is_correct: Optional[bool] = None
    comment: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    pass 

class FeedbackOut(FeedbackBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_model = True



#AUTHENTICATION

class LoginRequest(BaseModel):
    email:str
    password: str

class Token(BaseModel):
    access_token:str
    token_type: str = "bearer"