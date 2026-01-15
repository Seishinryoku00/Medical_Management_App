from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.models import doctor as doctor_models
from backend.app.models import patient as patient_models
from backend.database import get_db

# Configurazione
SECRET_KEY = "your-secret-key-change-in-production-min-32-chars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 ore

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica la password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera hash della password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decodifica un JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_patient(db: Session, email: str, password: str):
    """Autentica un paziente"""
    patient = db.query(patient_models.Patient).filter(patient_models.Patient.email == email).first()
    
    if not patient:
        return None
    if not patient.attivo:
        return None
    if not verify_password(password, patient.password_hash):
        return None
    
    return patient

def authenticate_doctor(db: Session, email: str, password: str):
    """Autentica un medico"""
    doctor = db.query(doctor_models.Doctor).filter(doctor_models.Doctor.email == email).first()
    
    if not doctor:
        return None
    if not doctor.attivo:
        return None
    if not verify_password(password, doctor.password_hash):
        return None
    
    return doctor

# Dependency per ottenere l'utente corrente dal token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Ottiene l'utente corrente dal token JWT"""
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id_str = payload.get("sub")
    user_type: str = payload.get("type")
    
    if user_id_str is None or user_type is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert string to int for database query
    user_id = int(user_id_str)
    
    if user_type == "patient":
        user = db.query(patient_models.Patient).filter(patient_models.Patient.id == user_id).first()
    elif user_type == "doctor":
        user = db.query(doctor_models.Doctor).filter(doctor_models.Doctor.id == user_id).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo utente non valido",
        )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non trovato",
        )
    
    if not user.attivo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disattivato",
        )
    
    # Aggiungi il tipo di utente all'oggetto
    user.user_type = user_type
    return user

# Dependency per richiedere che l'utente sia un paziente
async def get_current_patient(current_user = Depends(get_current_user)):
    """Verifica che l'utente corrente sia un paziente"""
    if not hasattr(current_user, 'user_type') or current_user.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso consentito solo ai pazienti",
        )
    return current_user

# Dependency per richiedere che l'utente sia un medico
async def get_current_doctor(current_user = Depends(get_current_user)):
    """Verifica che l'utente corrente sia un medico"""
    if not hasattr(current_user, 'user_type') or current_user.user_type != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso consentito solo ai medici",
        )
    return current_user

# Dependency opzionale - può essere paziente O medico
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Ottiene l'utente corrente ma non è obbligatorio"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
