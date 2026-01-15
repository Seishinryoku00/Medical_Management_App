
from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class AvailableSlot(BaseModel):
    data: date
    ora: time
    doctor_id: int
    nome_medico: str
    room_id: Optional[int] = None

class Message(BaseModel):
    message: str