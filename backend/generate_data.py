import random
from datetime import datetime, date, time, timedelta
from faker import Faker
from backend.database import SessionLocal
from backend.app import models
from backend.app.auth.auth_service import get_password_hash

fake = Faker('it_IT')

# Password di default per tutti gli utenti
DEFAULT_PASSWORD = "password123"

def generate_codice_fiscale():
    """Genera un codice fiscale fittizio"""
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    return ''.join(random.choices(letters, k=6)) + \
           ''.join(random.choices(digits, k=2)) + \
           random.choice(letters) + \
           ''.join(random.choices(digits, k=2)) + \
           random.choice(letters) + \
           ''.join(random.choices(digits, k=3)) + \
           random.choice(letters)

def generate_doctors(db):
    """Genera medici con diverse specializzazioni"""
    specializzazioni = [
        'Cardiologia', 'Dermatologia', 'Ortopedia', 'Pediatria',
        'Ginecologia', 'Neurologia', 'Oculistica', 'Psichiatria',
        'Medicina Generale', 'Endocrinologia'
    ]
    
    giorni_options = [
        'lun,mar,mer,gio,ven',
        'lun,mer,ven',
        'mar,gio',
        'lun,mar,gio,ven'
    ]
    
    doctors = []
    password_hash = get_password_hash(DEFAULT_PASSWORD)
    
    for i, spec in enumerate(specializzazioni):
        doctor = models.Doctor(
            nome=fake.first_name(),
            cognome=fake.last_name(),
            specializzazione=spec,
            email=f"dott.{fake.user_name()}@clinica.it",
            password_hash=password_hash,
            telefono=fake.phone_number(),
            orario_inizio=time(9, 0),
            orario_fine=time(18, 0) if i % 2 == 0 else time(17, 0),
            giorni_disponibili=random.choice(giorni_options)
        )
        doctors.append(doctor)
        db.add(doctor)
    
    db.commit()
    print(f"✓ Creati {len(doctors)} medici")
    print(f"  Email esempio: {doctors[0].email}")
    print(f"  Password per tutti: {DEFAULT_PASSWORD}")
    return doctors

def generate_patients(db, n=100):
    """Genera pazienti con dati completi"""
    patients = []
    password_hash = get_password_hash(DEFAULT_PASSWORD)
    
    for _ in range(n):
        patient = models.Patient(
            nome=fake.first_name(),
            cognome=fake.last_name(),
            codice_fiscale=generate_codice_fiscale(),
            data_nascita=fake.date_of_birth(minimum_age=18, maximum_age=90),
            email=fake.email(),
            password_hash=password_hash,
            telefono=fake.phone_number(),
            indirizzo=fake.street_address(),
            citta=fake.city(),
            cap=fake.postcode(),
            contatto_emergenza_nome=fake.name(),
            contatto_emergenza_telefono=fake.phone_number(),
            note_mediche=fake.text(max_nb_chars=200) if random.random() > 0.7 else None
        )
        patients.append(patient)
        db.add(patient)
    
    db.commit()
    print(f"Creati {len(patients)} pazienti")
    print(f"Email esempio: {patients[0].email}")
    print(f"Password per tutti: {DEFAULT_PASSWORD}")
    return patients

def generate_appointments(db, doctors, patients, rooms):
    """Genera appuntamenti realistici degli ultimi 3 mesi"""
    tipi_visita = [
        'Visita di controllo', 'Prima visita', 'Visita specialistica',
        'Visita urgente', 'Controllo post-operatorio', 'Consulto',
        'Esame diagnostico', 'Visita di routine'
    ]
    
    stati_probabilities = {
        'completato': 0.7,
        'programmato': 0.25,
        'cancellato': 0.05
    }
    
    appointments = []
    start_date = date.today() - timedelta(days=90)
    end_date = date.today() + timedelta(days=30)
    
    # Genera appuntamenti per ogni medico
    for doctor in doctors:
        giorni_map = {
            'lun': 0, 'mar': 1, 'mer': 2, 'gio': 3, 'ven': 4, 'sab': 5, 'dom': 6
        }
        giorni_disponibili = [giorni_map[g] for g in doctor.giorni_disponibili.split(',')]
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in giorni_disponibili:
                # Numero random di appuntamenti per giorno (3-7)
                n_appointments = random.randint(3, 7)
                
                for _ in range(n_appointments):
                    # Genera orario casuale nelle ore disponibili
                    ora_inizio_dt = datetime.combine(date.today(), doctor.orario_inizio)
                    ora_fine_dt = datetime.combine(date.today(), doctor.orario_fine)
                    
                    # Slot di 30 minuti
                    total_slots = int((ora_fine_dt - ora_inizio_dt).total_seconds() / 1800)
                    if total_slots > 0:
                        slot = random.randint(0, total_slots - 1)
                        ora = (ora_inizio_dt + timedelta(minutes=30 * slot)).time()
                        
                        # Determina stato basato sulla data
                        if current_date < date.today():
                            stato = random.choices(
                                ['completato', 'cancellato'],
                                weights=[0.93, 0.07]
                            )[0]
                        elif current_date == date.today():
                            stato = 'programmato'
                        else:
                            stato = 'programmato'
                        
                        appointment = models.Appointment(
                            doctor_id=doctor.id,
                            patient_id=random.choice(patients).id,
                            room_id=random.choice(rooms).id if random.random() > 0.1 else None,
                            data_appuntamento=current_date,
                            ora_inizio=ora,
                            durata_minuti=random.choice([30, 45, 60]),
                            tipo_visita=random.choice(tipi_visita),
                            stato=stato,
                            note=fake.sentence() if random.random() > 0.6 else None,
                            motivo_cancellazione=fake.sentence() if stato == 'cancellato' else None
                        )
                        appointments.append(appointment)
                        db.add(appointment)
            
            current_date += timedelta(days=1)
    
    db.commit()
    print(f"✓ Creati {len(appointments)} appuntamenti")
    return appointments

def main():
    """Funzione principale per generare tutti i dati"""
    print("Generazione dati per Sistema Gestione Studio Medico")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Ottieni le sale già create dallo schema
        rooms = db.query(models.Room).all()
        print(f"✓ Trovate {len(rooms)} sale visita")
        
        # Genera dati
        print("Generazione medici...")
        doctors = generate_doctors(db)
        
        print("Generazione pazienti...")
        patients = generate_patients(db, n=100)
        
        print("Generazione appuntamenti...")
        appointments = generate_appointments(db, doctors, patients, rooms)
        
        # Statistiche finali
        print("" + "=" * 50)
        print("RIEPILOGO")
        print("=" * 50)
        print(f"Medici creati: {len(doctors)}")
        print(f"Pazienti creati: {len(patients)}")
        print(f"Sale visita: {len(rooms)}")
        print(f"Appuntamenti creati: {len(appointments)}")
        
        # Statistiche appuntamenti
        stati = {}
        for apt in appointments:
            stati[apt.stato] = stati.get(apt.stato, 0) + 1
        
        print("Appuntamenti per stato:")
        for stato, count in stati.items():
            print(f"  - {stato}: {count}")
        
        print("Generazione completata con successo!")
        
    except Exception as e:
        print(f"Errore durante la generazione: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()