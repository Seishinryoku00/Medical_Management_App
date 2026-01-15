from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configurazione database MySQL
DATABASE_URL = "mysql+pymysql://root:56583W45lol**@localhost:3306/medical_management"

# Crea engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Crea sessione
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base per i modelli
Base = declarative_base()

# Dependency per ottenere la sessione database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()