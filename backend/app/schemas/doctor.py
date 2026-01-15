from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import time, datetime

class DoctorBase(BaseModel):
    nome: str
    cognome: str
    specializzazione: str
    email: EmailStr
    telefono: Optional[str] = None
    orario_inizio: time
    orario_fine: time
    giorni_disponibili: str

class DoctorCreate(DoctorBase):
    password: str

class Doctor(DoctorBase):
    id: int
    attivo: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class DoctorPublic(BaseModel):
    """Schema pubblico per medici (senza dati sensibili)"""
    id: int
    nome: str
    cognome: str
    specializzazione: str
    telefono: Optional[str]
    
    class Config:
        from_attributes = True
