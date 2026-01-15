from sqlalchemy import Column, Integer, String, Date, Time, Text, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    data_appuntamento = Column(Date, nullable=False, index=True)
    ora_inizio = Column(Time, nullable=False)
    durata_minuti = Column(Integer, nullable=False, default=30)
    tipo_visita = Column(String(100), nullable=False)
    stato = Column(
        Enum('programmato', 'completato', 'cancellato', 'in_attesa', name='stato_enum'),
        default='programmato',
        index=True
    )
    note = Column(Text)
    motivo_cancellazione = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    room = relationship("Room", back_populates="appointments")