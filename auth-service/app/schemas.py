from pydantic import BaseModel, EmailStr

class RegisterIn(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None

class LoginIn(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr | None

    class Config:
        from_attributes = True
