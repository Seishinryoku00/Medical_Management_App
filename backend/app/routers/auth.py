from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from backend.app import models
from backend.app.schemas.doctor import Doctor, DoctorCreate
from backend.app.schemas.auth import Token
from backend.app.schemas.auth import UserLogin
from backend.app.schemas.patient import Patient, PatientCreate
from backend.database import get_db
from backend.app.auth.auth_service import (
    authenticate_patient,
    authenticate_doctor,
    create_access_token,
    get_password_hash,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


@router.post("/login/patient", response_model=Token)
def login_patient(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login per pazienti"""
    patient = authenticate_patient(db, user_login.email, user_login.password)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(patient.id), "type": "patient"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "patient",
        "user_id": patient.id,
        "nome": patient.nome,
        "cognome": patient.cognome
    }

@router.post("/login/doctor", response_model=Token)
def login_doctor(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login per medici"""
    doctor = authenticate_doctor(db, user_login.email, user_login.password)
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(doctor.id), "type": "doctor"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "doctor",
        "user_id": doctor.id,
        "nome": doctor.nome,
        "cognome": doctor.cognome
    }

@router.post("/register/patient", response_model=Patient)
def register_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
    """Registrazione nuovo paziente"""
    # Verifica se email esiste già
    existing = db.query(models.Patient).filter(
        models.Patient.email == patient_data.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata"
        )
    
    # Verifica codice fiscale
    existing_cf = db.query(models.Patient).filter(
        models.Patient.codice_fiscale == patient_data.codice_fiscale
    ).first()
    if existing_cf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codice fiscale già registrato"
        )
    
    # Crea paziente
    patient_dict = patient_data.dict()
    password = patient_dict.pop('password')
    patient_dict['password_hash'] = get_password_hash(password)
    
    db_patient = models.Patient(**patient_dict)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    return db_patient

@router.post("/register/doctor", response_model=Doctor)
def register_doctor(doctor_data: DoctorCreate, db: Session = Depends(get_db)):
    """Registrazione nuovo medico"""
    # Verifica se email esiste già
    existing = db.query(models.Doctor).filter(
        models.Doctor.email == doctor_data.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata"
        )
    
    # Crea medico
    doctor_dict = doctor_data.dict()
    password = doctor_dict.pop('password')
    doctor_dict['password_hash'] = get_password_hash(password)
    
    db_doctor = models.Doctor(**doctor_dict)
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    
    return db_doctor

@router.get("/me")
def get_current_user_info(current_user = Depends(get_current_user)):
    """Ottiene informazioni sull'utente corrente"""
    user_info = {
        "id": current_user.id,
        "nome": current_user.nome,
        "cognome": current_user.cognome,
        "email": current_user.email,
        "user_type": current_user.user_type
    }
    
    if current_user.user_type == "patient":
        user_info.update({
            "codice_fiscale": current_user.codice_fiscale,
            "data_nascita": str(current_user.data_nascita),
            "telefono": current_user.telefono
        })
    elif current_user.user_type == "doctor":
        user_info.update({
            "specializzazione": current_user.specializzazione,
            "telefono": current_user.telefono
        })
    
    return user_info