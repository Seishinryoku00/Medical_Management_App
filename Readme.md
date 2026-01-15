# 🏥 Sistema di Gestione Studio Medico

Sistema completo per la gestione di appuntamenti, pazienti e medici con interfacce dedicate per pazienti e personale medico.

## Requisiti

- **Python 3.8+**
- **MySQL 8.0+**
- Browser moderno (Chrome, Firefox, Edge)

---

## Installazione Rapida

### 1. Setup Database MySQL

```sql
-- Da MySQL Workbench o terminale MySQL
CREATE DATABASE medical_management;
```

Poi importa lo schema:
```powershell
# Da PowerShell nella cartella del progetto
Get-Content database\schema.sql | mysql -u root -p medical_management
```

### 2. Configura Credenziali Database

Modifica `backend/database.py` linea 6:
```python
DATABASE_URL = "mysql+pymysql://root:TUA_PASSWORD@localhost:3306/medical_management"
```

### 3. Installa Dipendenze

```powershell
# Crea ambiente virtuale (se non esiste)
python -m venv .venv

# Attiva ambiente virtuale
.\.venv\Scripts\Activate.ps1

# Installa dipendenze
pip install -r requirements.txt
```

### 4. Genera Dati di Test

```powershell
python -m backend.generate_data
```

Questo crea: 10 medici, 100 pazienti, 5 sale e appuntamenti degli ultimi 3 mesi.

---

## Avvio Applicazione

### Backend API

```powershell
# Dalla cartella root del progetto (con venv attivo)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- **API**: http://localhost:8000
- **Documentazione Swagger**: http://localhost:8000/docs

### Frontend

```powershell
# In un nuovo terminale, dalla cartella frontend
cd frontend
python -m http.server 8080
```

- **Login**: http://localhost:8080/login.html
- **Portale Pazienti**: http://localhost:8080/index.html
- **Portale Medici**: http://localhost:8080/admin.html

---

## Credenziali di Test

Dopo la generazione dei dati, tutti gli utenti hanno la stessa password:

| Tipo | Email | Password |
|------|-------|----------|
| Paziente | *(vai su /docs → GET /api/patients/)* | `password123` |
| Medico | *(vai su /docs → GET /api/doctors/)* | `password123` |

---

## API Endpoints Principali

### Autenticazione
- `POST /api/auth/login/patient` - Login paziente
- `POST /api/auth/login/doctor` - Login medico
- `GET /api/auth/me` - Info utente corrente

### Medici
- `GET /api/doctors/` - Lista medici
- `GET /api/doctors/{id}/availability` - Disponibilità

### Pazienti
- `GET /api/patients/` - Lista pazienti (solo medici)
- `GET /api/patients/{id}/history` - Storico visite

### Appuntamenti
- `GET /api/appointments/` - Lista appuntamenti
- `POST /api/appointments/` - Crea appuntamento
- `DELETE /api/appointments/{id}` - Cancella (min 24h preavviso)
- `GET /api/appointments/available-slots` - Slot disponibili

### Sale
- `GET /api/rooms/` - Lista sale
- `GET /api/rooms/{id}/availability` - Disponibilità sala

---

## Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| Errore connessione DB | Verifica MySQL attivo e credenziali in `database.py` |
| Porta già in uso | Cambia porta: `--port 8001` |
| CORS error | Il backend accetta tutte le origini in sviluppo |

---

## Tecnologie

- **Backend**: FastAPI, SQLAlchemy, PyMySQL, JWT
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Database**: MySQL 8.0