from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime, timedelta
from backend.app import models
from backend.app.schemas import doctor as schemas
from backend.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.Doctor])
def get_doctors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutti i medici"""
    doctors = db.query(models.Doctor).offset(skip).limit(limit).all()
    return doctors

@router.get("/{doctor_id}", response_model=schemas.Doctor)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un medico specifico"""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    return doctor

@router.get("/specialization/{specialization}", response_model=List[schemas.Doctor])
def get_doctors_by_specialization(specialization: str, db: Session = Depends(get_db)):
    """Ottieni tutti i medici per una specifica specializzazione"""
    doctors = db.query(models.Doctor).filter(
        models.Doctor.specializzazione == specialization
    ).all()
    return doctors

@router.get("/{doctor_id}/availability")
def get_doctor_availability(
    doctor_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Ottieni disponibilità di un medico in un intervallo di date"""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    
    # Ottieni appuntamenti esistenti
    appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.data_appuntamento >= start_date,
        models.Appointment.data_appuntamento <= end_date,
        models.Appointment.stato != 'cancellato'
    ).all()
    
    # Crea mappa degli appuntamenti
    busy_slots = {}
    for apt in appointments:
        key = f"{apt.data_appuntamento}_{apt.ora_inizio}"
        busy_slots[key] = True
    
    # Genera slot disponibili
    available_slots = []
    giorni_map = {
        'lun': 0, 'mar': 1, 'mer': 2, 'gio': 3, 'ven': 4, 'sab': 5, 'dom': 6
    }
    giorni_disponibili = [giorni_map[g] for g in doctor.giorni_disponibili.split(',')]
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in giorni_disponibili:
            # Genera slot orari (ogni 30 minuti)
            ora_corrente = datetime.combine(date.today(), doctor.orario_inizio)
            ora_fine = datetime.combine(date.today(), doctor.orario_fine)
            
            while ora_corrente < ora_fine:
                slot_key = f"{current_date}_{ora_corrente.time()}"
                if slot_key not in busy_slots:
                    available_slots.append({
                        "data": str(current_date),
                        "ora": str(ora_corrente.time()),
                        "doctor_id": doctor_id,
                        "nome_medico": f"{doctor.nome} {doctor.cognome}"
                    })
                ora_corrente += timedelta(minutes=30)
        
        current_date += timedelta(days=1)
    
    return {
        "doctor": {
            "id": doctor.id,
            "nome": f"{doctor.nome} {doctor.cognome}",
            "specializzazione": doctor.specializzazione
        },
        "available_slots": available_slots
    }

@router.post("/", response_model=schemas.Doctor)
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)):
    """Crea un nuovo medico"""
    db_doctor = models.Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor