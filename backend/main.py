from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import doctors, patients, appointments, rooms, auth

# Inizializza FastAPI
app = FastAPI(
    title="Medical Management System API",
    description="Sistema di gestione per studio medico con autenticazione JWT",
    version="2.0.0"
)

# Middleware CORS (sviluppo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Auth
# Nota: i path dentro auth.router NON devono avere il prefisso /api/auth
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticazione"])

# Altri router
app.include_router(doctors.router, prefix="/api/doctors", tags=["Medici"])
app.include_router(patients.router, prefix="/api/patients", tags=["Pazienti"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appuntamenti"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["Sale Visita"])

# Root semplice
@app.get("/")
def read_root():
    return {
        "message": "Medical Management System API with JWT Authentication",
        "version": "2.0.0",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}