from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.sql import func
from backend.database import Base

class WaitingList(Base):
    __tablename__ = "waiting_list"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    specializzazione = Column(String(100), index=True)
    tipo_visita = Column(String(100), nullable=False)
    priorita = Column(
        Enum('bassa', 'media', 'alta', 'urgente', name='priorita_enum'),
        default='media',
        index=True
    )
    note = Column(Text)
    data_richiesta = Column(TIMESTAMP, server_default=func.now())
    notificato = Column(Boolean, default=False)