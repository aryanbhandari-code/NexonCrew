from sqlmodel import SQLModel, Field, create_engine
from typing import Optional
from datetime import date
import os

class Patient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_email: str = Field(index=True) # REMOVED unique=True so they can have multiple past orders
    patient_name: str
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    allergies: str
    past_diseases: str
    needs_refill_for: Optional[str] = None 
    refill_due_date: Optional[date] = None
    refill_trigger: Optional[bool] = False # <-- NEW: Maps to your new dataset column

class Medicine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str
    stock_quantity: int
    requires_prescription: bool = False
    expiry_date: Optional[date] = None

    # --- DATABASE CONNECTION ENGINE ---
if os.getenv("RAILWAY_ENVIRONMENT"):
    # Save to the permanent Railway volume
    sqlite_url = "sqlite:////app/data/nexus_pharmacy.db"
else:
    # Save locally on your laptop
    sqlite_url = "sqlite:///nexus_pharmacy.db"

engine = create_engine(sqlite_url)
