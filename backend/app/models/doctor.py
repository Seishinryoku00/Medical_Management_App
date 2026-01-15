from sqlalchemy import Column, Integer, String, Time, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cognome = Column(String(100), nullable=False)
    specializzazione = Column(String(100), nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    telefono = Column(String(20))
    orario_inizio = Column(Time, nullable=False)
    orario_fine = Column(Time, nullable=False)
    giorni_disponibili = Column(String(50), nullable=False)
    attivo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    appointments = relationship("Appointment", back_populates="doctor")