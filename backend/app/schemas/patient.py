from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

class PatientBase(BaseModel):
    nome: str
    cognome: str
    codice_fiscale: str
    data_nascita: date
    email: EmailStr
    telefono: str
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    contatto_emergenza_nome: Optional[str] = None
    contatto_emergenza_telefono: Optional[str] = None
    note_mediche: Optional[str] = None

class PatientCreate(PatientBase):
    password: str

class Patient(PatientBase):
    id: int
    attivo: bool
    created_at: datetime
    
    class Config:
        from_attributes = True