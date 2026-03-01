import csv
from sqlmodel import Session, SQLModel
from datetime import datetime
from models import Medicine, Patient
from database import engine

def build_database():
    # Automatically drops the old database tables and creates fresh ones
    print("🔄 Wiping old database and building new schema...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # --- 1. INGEST MEDICINES ---
        print("📦 Ingesting live inventory from products_policy_ready11_final.csv...")
        try:
            with open('products_policy_ready11_final.csv', mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse the expiry date safely
                    raw_exp = row.get('expiry_date')
                    exp_date = None
                    if raw_exp and str(raw_exp).lower() != 'nan':
                        try:
                            # Safely extract the date (e.g., "10/16/2026")
                            exp_date = datetime.strptime(str(raw_exp).split(' ')[0], "%m/%d/%Y").date()
                        except ValueError:
                            pass

                    med = Medicine(
                        name=row.get('product_name', 'Unknown'),
                        description=row.get('descriptions', 'Pharmacy Item'),
                        stock_quantity=int(float(row.get('current_stock', 0))),
                        requires_prescription=str(row.get('prescription_required', 'False')).lower() == 'true',
                        expiry_date=exp_date
                    )
                    session.add(med)
        except FileNotFoundError:
            print("❌ ERROR: Could not find products_policy_ready11_final.csv")
            return

        # --- 2. INGEST PATIENT ORDERS ---
        print("🧑‍⚕️ Ingesting patient history from order_history_intelligence_ready11_final.csv...")
        try:
            with open('order_history_intelligence_ready11_final.csv', mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    
                    # Parse the exact date the patient will run out of medicine
                    raw_runout = row.get('expected_runout_date')
                    runout_date = None
                    if raw_runout and str(raw_runout).lower() != 'nan':
                        try:
                            # Safely extract the date (e.g., "3/16/2024 0:00" -> "3/16/2024")
                            date_str = str(raw_runout).split(' ')[0]
                            runout_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                        except ValueError:
                            pass
                    
                    # Identify if this data row flagged them for a refill
                    is_trigger = str(row.get('refill_trigger', 'False')).lower() == 'true'

                    # Handle empty age fields safely
                    raw_age = row.get('patient_age')
                    patient_age = int(float(raw_age)) if raw_age and str(raw_age).lower() != 'nan' else 0

                    patient = Patient(
                        patient_email=row.get('patient_email', f"patient{idx}@example.com"),
                        patient_name=row.get('patient_id', 'Unknown'),
                        patient_age=patient_age,
                        patient_gender=row.get('patient_gender', ''),
                        allergies=row.get('allergies', ''),
                        past_diseases=row.get('past_diseases', ''),
                        needs_refill_for=row.get('product_name', ''),
                        refill_due_date=runout_date,
                        refill_trigger=is_trigger
                    )
                    session.add(patient)
        except FileNotFoundError:
            print("❌ ERROR: Could not find order_history_intelligence_ready11_final.csv")
            return
        
        # Commit all the new data to the SQLite database
        session.commit()
        print("✅ SUCCESS: Database successfully rebuilt with new augmented dataset!")

if __name__ == "__main__":
    build_database()