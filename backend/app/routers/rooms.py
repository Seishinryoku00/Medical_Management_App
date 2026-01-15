from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from backend.app import models
from backend.app.schemas import room as schemas
from backend.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.Room])
def get_rooms(
    skip: int = 0,
    limit: int = 100,
    attiva: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Ottieni lista di tutte le sale visita"""
    query = db.query(models.Room)
    
    if attiva is not None:
        query = query.filter(models.Room.attiva == attiva)
    
    rooms = query.offset(skip).limit(limit).all()
    return rooms

@router.get("/{room_id}", response_model=schemas.Room)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una sala specifica"""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala non trovata")
    return room

@router.get("/{room_id}/availability")
def get_room_availability(
    room_id: int,
    data: date,
    db: Session = Depends(get_db)
):
    """Ottieni disponibilità di una sala per una data specifica"""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala non trovata")
    
    if not room.attiva:
        return {
            "room": {
                "id": room.id,
                "numero": room.numero,
                "nome": room.nome
            },
            "available": False,
            "reason": "Sala non attiva",
            "appointments": []
        }
    
    # Ottieni appuntamenti per quella data
    appointments = db.query(models.Appointment).filter(
        models.Appointment.room_id == room_id,
        models.Appointment.data_appuntamento == data,
        models.Appointment.stato != 'cancellato'
    ).order_by(models.Appointment.ora_inizio).all()
    
    appointment_list = []
    for apt in appointments:
        doctor = db.query(models.Doctor).filter(models.Doctor.id == apt.doctor_id).first()
        patient = db.query(models.Patient).filter(models.Patient.id == apt.patient_id).first()
        
        appointment_list.append({
            "id": apt.id,
            "ora_inizio": str(apt.ora_inizio),
            "durata_minuti": apt.durata_minuti,
            "tipo_visita": apt.tipo_visita,
            "medico": f"{doctor.nome} {doctor.cognome}",
            "paziente": f"{patient.nome} {patient.cognome}"
        })
    
    return {
        "room": {
            "id": room.id,
            "numero": room.numero,
            "nome": room.nome,
            "attrezzature": room.attrezzature
        },
        "data": str(data),
        "available": room.attiva,
        "appointments": appointment_list,
        "total_appointments": len(appointment_list)
    }