from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WaitingListBase(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    specializzazione: Optional[str] = None
    tipo_visita: str
    priorita: str = "media"
    note: Optional[str] = None

class WaitingListCreate(WaitingListBase):
    pass

class WaitingList(WaitingListBase):
    id: int
    data_richiesta: datetime
    notificato: bool
    
    class Config:
        from_attributes = True