from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app import models
from backend.app.schemas import patient as schemas
from backend.database import get_db
from backend.app.auth.auth_service import get_current_doctor, get_current_patient, get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.Patient])
def get_patients(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    current_user = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Ottieni lista pazienti - Solo per medici"""
    query = db.query(models.Patient)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Patient.nome.like(search_filter)) |
            (models.Patient.cognome.like(search_filter)) |
            (models.Patient.codice_fiscale.like(search_filter))
        )
    
    patients = query.offset(skip).limit(limit).all()
    return patients

@router.get("/me", response_model=schemas.Patient)
def get_my_profile(current_user = Depends(get_current_patient), db: Session = Depends(get_db)):
    """Ottieni il proprio profilo - Solo pazienti"""
    return current_user

@router.get("/{patient_id}", response_model=schemas.Patient)
def get_patient(
    patient_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni dettagli paziente - Medici vedono tutti, pazienti solo se stessi"""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    
    # Se è un paziente, può vedere solo i propri dati
    if hasattr(current_user, 'user_type') and current_user.user_type == "patient":
        if patient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non puoi accedere ai dati di altri pazienti")
    
    return patient

@router.get("/{patient_id}/history")
def get_patient_history(
    patient_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni storico visite - Medici vedono tutto, pazienti solo proprie"""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    
    # Verifica permessi
    if hasattr(current_user, 'user_type') and current_user.user_type == "patient":
        if patient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non puoi accedere allo storico di altri pazienti")
    
    # Ottieni tutti gli appuntamenti del paziente
    appointments = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id
    ).order_by(models.Appointment.data_appuntamento.desc()).all()
    
    # Arricchisci con dati medico
    history = []
    for apt in appointments:
        doctor = db.query(models.Doctor).filter(models.Doctor.id == apt.doctor_id).first()
        history.append({
            "id": apt.id,
            "data": str(apt.data_appuntamento),
            "ora": str(apt.ora_inizio),
            "tipo_visita": apt.tipo_visita,
            "stato": apt.stato,
            "medico": f"{doctor.nome} {doctor.cognome}",
            "specializzazione": doctor.specializzazione,
            "note": apt.note
        })
    
    return {
        "patient": {
            "id": patient.id,
            "nome": f"{patient.nome} {patient.cognome}",
            "codice_fiscale": patient.codice_fiscale
        },
        "history": history,
        "total_visits": len(history)
    }

@router.post("/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Crea un nuovo paziente - Endpoint pubblico per registrazione"""
    # Verifica se codice fiscale già esiste
    existing = db.query(models.Patient).filter(
        models.Patient.codice_fiscale == patient.codice_fiscale
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Codice fiscale già registrato")
    
    # Verifica se email già esiste
    existing_email = db.query(models.Patient).filter(
        models.Patient.email == patient.email
    ).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.put("/{patient_id}", response_model=schemas.Patient)
def update_patient(
    patient_id: int,
    patient: schemas.PatientCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggiorna dati paziente - Solo se stesso o medico"""
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    
    # Verifica permessi
    if hasattr(current_user, 'user_type') and current_user.user_type == "patient":
        if patient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non puoi modificare i dati di altri pazienti")
    
    for key, value in patient.dict().items():
        setattr(db_patient, key, value)
    
    db.commit()
    db.refresh(db_patient)
    return db_patient