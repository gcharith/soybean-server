from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    Text
)
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    #columns
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable = False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable = False)
    created_at = Column(DateTime, default=datetime.utcnow)


    #relationships
    predictions = relationship("Prediction", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")

class Prediction(Base):
    __tablename__ = "predictions"

    #columns
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String, nullable=False)
    predicted_label = Column(String, nullable=False)
    confidence = Column(Float)
    model_version = Column(String, default="resnet50_v1")
    created_at = Column(DateTime, default=datetime.utcnow)

    #relationships
    user = relationship("User", back_populates="predictions")
    feedbacks = relationship("Feedback", back_populates="prediction")

class Feedback(Base):
    __tablename__ = "feedbacks"

    #columns
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    rating = Column(Integer, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    #relationships
    user = relationship("User", back_populates="feedbacks")
    prediction = relationship("Prediction",back_populates="feedbacks")
