from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_id: int
    nome: str
    cognome: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nome: str
    cognome: str