from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date, datetime, timedelta
from backend.app import models
from backend.app.schemas import appointment as schemas
from backend.database import get_db
from backend.app.auth.auth_service import get_current_user, get_current_patient

router = APIRouter()

MINIMUM_NOTICE_HOURS = 24

@router.get("/", response_model=List[schemas.Appointment])
def get_appointments(
    skip: int = 0,
    limit: int = 100,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    data_from: Optional[date] = None,
    data_to: Optional[date] = None,
    stato: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni lista appuntamenti con filtri - Solo i propri appuntamenti per i pazienti"""
    query = db.query(models.Appointment)
    
    # Se è un paziente, può vedere solo i propri appuntamenti
    if hasattr(current_user, 'user_type') and current_user.user_type == "patient":
        query = query.filter(models.Appointment.patient_id == current_user.id)
    
    # Se è un medico, può vedere solo i propri appuntamenti
    if hasattr(current_user, 'user_type') and current_user.user_type == "doctor":
        query = query.filter(models.Appointment.doctor_id == current_user.id)
    
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if data_from:
        query = query.filter(models.Appointment.data_appuntamento >= data_from)
    if data_to:
        query = query.filter(models.Appointment.data_appuntamento <= data_to)
    if stato:
        query = query.filter(models.Appointment.stato == stato)
    
    appointments = query.order_by(
        models.Appointment.data_appuntamento.desc(),
        models.Appointment.ora_inizio.desc()
    ).offset(skip).limit(limit).all()
    
    return appointments

@router.get("/detailed")
def get_appointments_detailed(
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    data: Optional[date] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni appuntamenti con dettagli completi - Autenticazione richiesta"""
    query = db.query(
        models.Appointment,
        models.Doctor,
        models.Patient,
        models.Room
    ).join(
        models.Doctor, models.Appointment.doctor_id == models.Doctor.id
    ).join(
        models.Patient, models.Appointment.patient_id == models.Patient.id
    ).outerjoin(
        models.Room, models.Appointment.room_id == models.Room.id
    )
    
    # Filtri basati sul tipo di utente
    if hasattr(current_user, 'user_type') and current_user.user_type == "patient":
        query = query.filter(models.Appointment.patient_id == current_user.id)
    elif hasattr(current_user, 'user_type') and current_user.user_type == "doctor":
        query = query.filter(models.Appointment.doctor_id == current_user.id)
    
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if data:
        query = query.filter(models.Appointment.data_appuntamento == data)
    
    results = query.all()
    
    detailed_appointments = []
    for apt, doctor, patient, room in results:
        detailed_appointments.append({
            "id": apt.id,
            "data_appuntamento": str(apt.data_appuntamento),
            "ora_inizio": str(apt.ora_inizio),
            "durata_minuti": apt.durata_minuti,
            "tipo_visita": apt.tipo_visita,
            "stato": apt.stato,
            "note": apt.note,
            "nome_medico": f"{doctor.nome} {doctor.cognome}",
            "specializzazione": doctor.specializzazione,
            "nome_paziente": f"{patient.nome} {patient.cognome}",
            "telefono_paziente": patient.telefono,
            "email_paziente": patient.email,
            "sala_numero": room.numero if room else None,
            "sala_nome": room.nome if room else None
        })
    
    return detailed_appointments

@router.get("/available-slots")
def get_available_slots(
    specializzazione: Optional[str] = None,
    doctor_id: Optional[int] = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    """Ottieni slot disponibili per specializzazione o medico"""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)
    
    # Filtra medici
    query = db.query(models.Doctor)
    if doctor_id:
        query = query.filter(models.Doctor.id == doctor_id)
    elif specializzazione:
        query = query.filter(models.Doctor.specializzazione == specializzazione)
    
    doctors = query.all()
    
    all_slots = []
    for doctor in doctors:
        # Ottieni appuntamenti esistenti
        appointments = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor.id,
            models.Appointment.data_appuntamento >= start_date,
            models.Appointment.data_appuntamento <= end_date,
            models.Appointment.stato != 'cancellato'
        ).all()
        
        busy_slots = {}
        for apt in appointments:
            key = f"{apt.data_appuntamento}_{apt.ora_inizio}"
            busy_slots[key] = True
        
        # Genera slot disponibili
        giorni_map = {
            'lun': 0, 'mar': 1, 'mer': 2, 'gio': 3, 'ven': 4, 'sab': 5, 'dom': 6
        }
        giorni_disponibili = [giorni_map[g] for g in doctor.giorni_disponibili.split(',')]
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in giorni_disponibili:
                ora_corrente = datetime.combine(date.today(), doctor.orario_inizio)
                ora_fine = datetime.combine(date.today(), doctor.orario_fine)
                
                while ora_corrente < ora_fine:
                    slot_key = f"{current_date}_{ora_corrente.time()}"
                    if slot_key not in busy_slots:
                        all_slots.append({
                            "data": str(current_date),
                            "ora": str(ora_corrente.time()),
                            "doctor_id": doctor.id,
                            "nome_medico": f"{doctor.nome} {doctor.cognome}",
                            "specializzazione": doctor.specializzazione
                        })
                    ora_corrente += timedelta(minutes=30)
            
            current_date += timedelta(days=1)
    
    return {"available_slots": all_slots, "total": len(all_slots)}

@router.get("/waiting-list")
def get_waiting_list(db: Session = Depends(get_db)):
    """Ottieni lista d'attesa"""
    waiting = db.query(models.WaitingList).order_by(
        models.WaitingList.priorita.desc(),
        models.WaitingList.data_richiesta
    ).all()
    
    result = []
    for item in waiting:
        patient = db.query(models.Patient).filter(models.Patient.id == item.patient_id).first()
        doctor = None
        if item.doctor_id:
            doctor = db.query(models.Doctor).filter(models.Doctor.id == item.doctor_id).first()
        
        result.append({
            "id": item.id,
            "paziente": f"{patient.nome} {patient.cognome}",
            "telefono": patient.telefono,
            "tipo_visita": item.tipo_visita,
            "specializzazione": item.specializzazione,
            "medico": f"{doctor.nome} {doctor.cognome}" if doctor else None,
            "priorita": item.priorita,
            "data_richiesta": str(item.data_richiesta),
            "note": item.note
        })
    
    return result

@router.get("/{appointment_id}", response_model=schemas.Appointment)
def get_appointment(
    appointment_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni un singolo appuntamento per ID"""
    db_appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()
    
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    # Verifica permessi: paziente può vedere solo i propri, medico solo i propri
    if hasattr(current_user, 'user_type'):
        if current_user.user_type == "patient" and db_appointment.patient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non hai accesso a questo appuntamento")
        elif current_user.user_type == "doctor" and db_appointment.doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non hai accesso a questo appuntamento")
    
    return db_appointment

@router.post("/", response_model=schemas.Appointment)
def create_appointment(
    appointment: schemas.AppointmentCreate,
    current_user = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Crea un nuovo appuntamento - Solo pazienti autenticati"""
    # Forza il patient_id dell'utente loggato
    if appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Puoi prenotare appuntamenti solo per te stesso"
        )
    
    # Verifica che medico esista
    doctor = db.query(models.Doctor).filter(models.Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    
    # Verifica disponibilità medico (no appuntamenti sovrapposti)
    ora_fine = (datetime.combine(date.today(), appointment.ora_inizio) + 
                timedelta(minutes=appointment.durata_minuti)).time()
    
    conflicting = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == appointment.doctor_id,
        models.Appointment.data_appuntamento == appointment.data_appuntamento,
        models.Appointment.stato != 'cancellato',
        or_(
            and_(
                models.Appointment.ora_inizio <= appointment.ora_inizio,
                models.Appointment.ora_inizio > appointment.ora_inizio
            ),
            and_(
                models.Appointment.ora_inizio < ora_fine,
                models.Appointment.ora_inizio >= appointment.ora_inizio
            )
        )
    ).first()
    
    if conflicting:
        raise HTTPException(status_code=409, detail="Orario non disponibile per questo medico")
    
    # Verifica disponibilità sala se specificata
    if appointment.room_id:
        room = db.query(models.Room).filter(models.Room.id == appointment.room_id).first()
        if not room or not room.attiva:
            raise HTTPException(status_code=404, detail="Sala non disponibile")
        
        room_conflict = db.query(models.Appointment).filter(
            models.Appointment.room_id == appointment.room_id,
            models.Appointment.data_appuntamento == appointment.data_appuntamento,
            models.Appointment.stato != 'cancellato',
            models.Appointment.ora_inizio == appointment.ora_inizio
        ).first()
        
        if room_conflict:
            raise HTTPException(status_code=409, detail="Sala non disponibile in questo orario")
    
    # Crea appuntamento
    db_appointment = models.Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@router.put("/{appointment_id}", response_model=schemas.Appointment)
def update_appointment(
    appointment_id: int,
    appointment_update: schemas.AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """Modifica un appuntamento esistente con preavviso minimo"""
    db_appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()
    
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    if db_appointment.stato == 'cancellato':
        raise HTTPException(status_code=400, detail="Non è possibile modificare un appuntamento cancellato")
    
    # Verifica preavviso minimo
    appointment_datetime = datetime.combine(
        db_appointment.data_appuntamento,
        db_appointment.ora_inizio
    )
    hours_until = (appointment_datetime - datetime.now()).total_seconds() / 3600
    
    if hours_until < MINIMUM_NOTICE_HOURS:
        raise HTTPException(
            status_code=400,
            detail=f"È necessario un preavviso di almeno {MINIMUM_NOTICE_HOURS} ore"
        )
    
    # Aggiorna campi
    for key, value in appointment_update.dict(exclude_unset=True).items():
        setattr(db_appointment, key, value)
    
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@router.delete("/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    motivo: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancella un appuntamento - Paziente può cancellare i propri, medico i propri"""
    db_appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()
    
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    
    # Verifica permessi
    if hasattr(current_user, 'user_type'):
        if current_user.user_type == "patient" and db_appointment.patient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non puoi cancellare appuntamenti di altri pazienti")
        elif current_user.user_type == "doctor" and db_appointment.doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non puoi cancellare appuntamenti di altri medici")
    
    if db_appointment.stato == 'cancellato':
        raise HTTPException(status_code=400, detail="Appuntamento già cancellato")
    
    # Verifica preavviso minimo
    appointment_datetime = datetime.combine(
        db_appointment.data_appuntamento,
        db_appointment.ora_inizio
    )
    hours_until = (appointment_datetime - datetime.now()).total_seconds() / 3600
    
    if hours_until < MINIMUM_NOTICE_HOURS:
        raise HTTPException(
            status_code=400,
            detail=f"È necessario un preavviso di almeno {MINIMUM_NOTICE_HOURS} ore"
        )
    
    # Aggiorna stato
    db_appointment.stato = 'cancellato'
    db_appointment.motivo_cancellazione = motivo
    db.commit()
    
    return {"message": "Appuntamento cancellato con successo"}