from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cognome = Column(String(100), nullable=False, index=True)
    codice_fiscale = Column(String(16), unique=True, nullable=False, index=True)
    data_nascita = Column(Date, nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    indirizzo = Column(String(255))
    citta = Column(String(100))
    cap = Column(String(10))
    contatto_emergenza_nome = Column(String(100))
    contatto_emergenza_telefono = Column(String(20))
    note_mediche = Column(Text)
    attivo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    appointments = relationship("Appointment", back_populates="patient")