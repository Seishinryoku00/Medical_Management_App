from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoomBase(BaseModel):
    numero: str
    nome: Optional[str] = None
    piano: Optional[int] = None
    attrezzature: Optional[str] = None
    capienza: int = 1
    attiva: bool = True

class Room(RoomBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
