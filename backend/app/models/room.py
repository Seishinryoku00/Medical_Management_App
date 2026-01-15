from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(10), unique=True, nullable=False, index=True)
    nome = Column(String(100))
    piano = Column(Integer)
    attrezzature = Column(Text)
    capienza = Column(Integer, default=1)
    attiva = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    appointments = relationship("Appointment", back_populates="room")