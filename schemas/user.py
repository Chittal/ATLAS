from pydantic import BaseModel

# Authentication models
class UserSignup(BaseModel):
    email: str
    password: str
    passwordConfirm: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str
