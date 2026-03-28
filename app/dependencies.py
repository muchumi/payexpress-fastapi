from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import session

from app.db.database import get_db
from app.models.user import User
from app.auth import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="could not validate credentials"
    )
    try:
        # decode JWT token to get the email of the user
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email=payload.get("sub")
        # validating if the email exists
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # querying the database to get the user with the email from the token
    user = db.query(User).filter(User.email==email).first()
    if user is None:
        raise credentials_exception
    return user  



