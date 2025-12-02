import os
from dotenv import load_dotenv
from datetime import datetime,timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str)->str:
    """Takes password and returns encrypted hash"""
    return pwd_context.hash(password)

def verify_password(plain_password:str, hash_password:str)->bool:
    """Verify if submitted password is correct"""
    return pwd_context.verify(plain_password, hash_password)

def create_access_token(data:dict, expires_delta:Optional[timedelta] = None)->str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
