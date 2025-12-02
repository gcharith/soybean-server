from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from deps import get_db
from security import SECRET_KEY, ALGORITHM
import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token:str = Depends(oauth2_scheme), db:Session = Depends(get_db)) -> models.User:
    """Gets current logged in user using token in authorization header and returns the user"""

    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str:str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user