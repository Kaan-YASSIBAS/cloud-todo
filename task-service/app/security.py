from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from .config import settings

security = HTTPBearer()

def verify_token(token: str, raise_exception: bool = False):
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return {"valid": True, "user": data.get("sub")}
    except jwt.ExpiredSignatureError:
        if raise_exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        return {"valid": False}
    except jwt.InvalidTokenError:
        if raise_exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"valid": False}

def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = creds.credentials
    res = verify_token(token, raise_exception=True)
    user = res.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user
