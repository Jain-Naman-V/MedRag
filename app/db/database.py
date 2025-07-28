from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DB_PATH = os.getenv("DB_PATH", "./data/MedRAG.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from your models file
from app.db.models import Base

def init_db():
    # Create all tables in the database
    # This will only create tables that don't already exist
    Base.metadata.create_all(bind=engine)
