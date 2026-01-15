from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime

class AppointmentBase(BaseModel):
    doctor_id: int
    patient_id: int
    room_id: Optional[int] = None
    data_appuntamento: date
    ora_inizio: time
    durata_minuti: int = 30
    tipo_visita: str
    note: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    data_appuntamento: Optional[date] = None
    ora_inizio: Optional[time] = None
    room_id: Optional[int] = None
    note: Optional[str] = None

class Appointment(AppointmentBase):
    id: int
    stato: str
    motivo_cancellazione: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AppointmentDetailed(BaseModel):
    id: int
    data_appuntamento: date
    ora_inizio: time
    durata_minuti: int
    tipo_visita: str
    stato: str
    note: Optional[str]
    nome_medico: str
    specializzazione: str
    nome_paziente: str
    telefono_paziente: str
    sala_numero: Optional[str]
    
    class Config:
        from_attributes = True