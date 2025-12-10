from datetime import datetime, timedelta, UTC
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from .config import settings

security = HTTPBearer()

def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=settings.ACCESS_EXPIRE_HOURS)
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str, raise_exception: bool = False):
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return {"valid": True, "user": data.get("sub")}
    except jwt.ExpiredSignatureError:
        if raise_exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        return {"valid": False, "reason": "expired"}
    except jwt.InvalidTokenError:
        if raise_exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"valid": False, "reason": "invalid"}

def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = creds.credentials
    res = verify_token(token, raise_exception=True)
    user = res.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user
