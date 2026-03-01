from crewai.tools import tool
from sqlmodel import Session, select, func
from database import engine
from models import Medicine, Patient
from datetime import date, timedelta
import requests

@tool("check_inventory_and_policy")
def check_inventory_and_policy(medicine_name: str) -> str:
    """Checks the SQLite database for stock levels and prescription requirements."""
    with Session(engine) as session:
        statement = select(Medicine).where(Medicine.name.contains(medicine_name))
        result = session.exec(statement).first()
        if result:
            return f"Found {result.name}: Stock is {result.stock_quantity}. Prescription required: {result.requires_prescription}."
        return f"Medicine '{medicine_name}' not found in inventory."

@tool("check_patient_history")
def check_patient_history(email: str) -> str:
    """
    Checks the SQLite database for the patient's medical history and allergies.
    
    Args:
        email (str): The exact email address of the patient to look up.
    """
    with Session(engine) as session:
        statement = select(Patient).where(Patient.patient_email == email)
        result = session.exec(statement).first() 
        if result:
            return f"Patient Name: {result.patient_name}, Age: {result.patient_age}, Allergies: {result.allergies}, Past Diseases: {result.past_diseases}."
        return "New patient. No medical history found."

@tool("trigger_fulfillment_webhook")
def trigger_fulfillment_webhook(order_details: str) -> str:
    """Simulates sending the final approved order to the warehouse logistics system."""
    print(f"\n[WEBHOOK FIRED TO WAREHOUSE] -> {order_details}\n")
    return "SUCCESS: Order transmitted to warehouse for packing."

@tool("analyze_historical_demand")
def analyze_historical_demand() -> str:
    """Scans historical past data to predict future medicine demand, patient course completions, and sales trends."""
    with Session(engine) as session:
        # 1. MACRO PREDICTION: Forecast future bulk orders based on current stock
        meds = session.exec(select(Medicine)).all()
        reorder_list = []
        for m in meds:
            if m.stock_quantity < 15:
                recommended_order = 50 - m.stock_quantity
                reorder_list.append(f"- {m.name}: Currently {m.stock_quantity} units. Forecasted order required: {recommended_order} units.")

        # 2. MICRO PREDICTION: Predict exact patient run-out dates based on past orders
        # Looking specifically for patients flagged by our historical dataset
        patients = session.exec(select(Patient).where(Patient.refill_trigger == True)).limit(5).all()
        course_completions = []
        for p in patients:
            if p.refill_due_date:
                course_completions.append(f"- Patient {p.patient_name} will exhaust '{p.needs_refill_for}' on {p.refill_due_date}. Action: Pre-approve 1 unit.")

        # 3. TREND PREDICTION: Identify Best-Selling Medicines (High-Velocity Stock)
        statement = select(Patient.needs_refill_for, func.count(Patient.id)).group_by(Patient.needs_refill_for).order_by(func.count(Patient.id).desc()).limit(3)
        top_medicines = session.exec(statement).all()
        trend_list = []
        for med_name, count in top_medicines:
            if med_name and str(med_name) != 'nan':
                trend_list.append(f"- {med_name}: {count} historical orders. Predictive Action: Increase standard inventory buffer by 25%.")

        report = "📊 HISTORICAL DEMAND & PREDICTIVE FORECAST\n\n"
        report += "📈 Sales Trend Analysis (High-Velocity Items):\n" + ("\n".join(trend_list) if trend_list else "Not enough data.") + "\n\n"
        report += "📦 Macro Stock Replenishment Forecast (Pharmacy Level):\n" + ("\n".join(reorder_list) if reorder_list else "All stock optimal.") + "\n\n"
        report += "🧑‍⚕️ Micro Patient Course Completions (Patient Level):\n" + ("\n".join(course_completions) if course_completions else "No immediate course completions forecasted.")
        
        return report
    
@tool("fetch_live_environmental_threats")
def fetch_live_environmental_threats() -> str:
    """Fetches real-time live weather data and active health outbreak news for the region."""
    
    # 1. REAL LIVE WEATHER API (Hardcoded to Solapur coordinates for the demo)
    try:
        # Latitude 17.6599, Longitude 75.9064 (Solapur, India)
        weather_url = "https://api.open-meteo.com/v1/forecast?latitude=17.6599&longitude=75.9064&current_weather=true"
        response = requests.get(weather_url).json()
        temp = response['current_weather']['temperature']
        windspeed = response['current_weather']['windspeed']
        
        weather_status = f"Live Weather Data for Solapur: {temp}°C, Windspeed: {windspeed} km/h."
        if temp > 35:
            weather_status += " ⚠️ WARNING: Severe Heatwave detected."
        elif temp < 15:
            weather_status += " ⚠️ WARNING: Cold wave detected."
    except Exception as e:
        weather_status = "Live Weather API unreachable. Defaulting to 38°C (Heatwave Warning)."

    # 2. LIVE OUTBREAK & NEWS FEED (Simulated for Hackathon safety)
    news_status = (
        "LIVE EPIDEMIOLOGICAL ALERTS:\n"
        "- 🚨 VIRUS ALERT: Localized outbreak of Viral Conjunctivitis (Pink Eye) reported in the district.\n"
        "- 🌫️ AQI ALERT: Air Quality Index is currently 165 (Unhealthy). High risk for asthma and COPD patients."
    )

    return f"🌍 LIVE ENVIRONMENTAL & OUTBREAK DATA:\n{weather_status}\n\n{news_status}"