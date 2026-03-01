from sqlmodel import create_engine, SQLModel

DB_FILE = "nexus_pharmacy.db"
sqlite_url = f"sqlite:///{DB_FILE}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)