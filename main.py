import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from crewai import Task, Crew
from sqlmodel import Session, select

# Import your local database engine and tables
from models import engine, Patient, Medicine

from vision import verify_prescription_with_gemini

# Import your custom tools and agents
from tools import check_patient_history, check_inventory_and_policy, trigger_fulfillment_webhook, analyze_historical_demand, fetch_live_environmental_threats
from agents import concierge_agent, safety_agent, compliance_agent, proactive_agent, environmental_agent

# --- 1. REAL GMAIL DISPATCHER SETUP ---
SENDER_EMAIL = "adityabhelande285@gmail.com"
# PUT YOUR GOOGLE APP PASSWORD BELOW (Keep the quotes, no spaces)
APP_PASSWORD = "cgjrejibzdgjmylr" 

def send_real_email(recipient_email, patient_name, medicine_name, due_date):
    """Securely connects to Gmail's SMTP server to send a real email."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = f"⚠️ URGENT: {medicine_name} Refill Required"
        
        body = f"Hello {patient_name},\n\nYour prescription for {medicine_name} is running low and will run out by {due_date}. Please reply to your Nexus Copilot to authorize an automated refill.\n\nStay healthy,\nNexus AI Pharmacy System"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Failed to send real email: {e}")
        return False

# --- 2. FASTAPI INITIALIZATION ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    text: str
    email: str

# --- 3. VISION & UPLOAD ROUTE ---
import google.generativeai as genai
import os

# 1. CONFIGURE GEMINI
# Replace with your actual Gemini API Key
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" 
genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. VISION & UPLOAD ROUTE (REAL AI EXTRACTION) ---
@app.post("/upload")
async def upload_rx(file: UploadFile = File(...)):
    """Reads prescription images using Gemini 2.5."""
    contents = await file.read()
    extracted_data = verify_prescription_with_gemini(contents)
    return {"status": "success", "extracted_text": extracted_data}

# --- 4. CORE CHAT & AGENTIC ROUTE ---
@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.text
    user_email = request.email

    task1 = Task(
        description=f"Analyze this user request: '{user_message}'. Extract the exact medicine name and quantity requested.",
        expected_output="The medicine name and requested quantity.",
        agent=concierge_agent
    )

    task2 = Task(
        description=f"Retrieve the medical history for the patient with email: {user_email}. Evaluate their record against the requested medicine to see if it is safe.",
        expected_output="A definitive safety approval or rejection based on the database facts.",
        agent=safety_agent
    )

    task3 = Task(
        description=(
            "Review the safety decision from Task 2. If approved, use the check_inventory_and_policy tool. "
            "If safe and in stock, use the trigger_fulfillment_webhook tool. "
            "CRITICAL INSTRUCTION: You MUST output your final answer using EXACTLY this template:\n\n"
            "<details style='background:#f1f5f9; padding:8px; border-radius:5px; margin-bottom:10px; font-size:12px; color:#475569;'>\n"
            "<summary style='cursor:pointer; font-weight:bold;'>🔍 View Agent Reasoning</summary>\n"
            "Briefly summarize the safety and inventory facts here in plain text.\n"
            "</details>\n\n"
            "[Insert your friendly, professional customer-facing message here confirming or rejecting the order.]\n\n"
            "ABSOLUTE RULE: NEVER output raw JSON, dictionaries (like {'medicine_name': ...}), or internal tool commands in your final text."
        ),
        expected_output="An HTML accordion and a friendly text message. No JSON or tool syntax allowed.",
        agent=compliance_agent
    )

    crew = Crew(
        agents=[concierge_agent, safety_agent, compliance_agent],
        tasks=[task1, task2, task3],
        verbose=True
    )

    result = crew.kickoff()
    return {"response": str(result)}

# --- 5. ADMIN & INVENTORY METRICS ROUTE ---
@app.get("/api/admin")
async def get_admin_data():
    with Session(engine) as session:
        medicines = session.exec(select(Medicine)).all()
        patients = session.exec(select(Patient)).all()

        total_meds = len(medicines)
        low_stock = sum(1 for m in medicines if m.stock_quantity < 15)
        out_of_stock = sum(1 for m in medicines if m.stock_quantity == 0)

        refills = [
            {
                "patient_name": p.patient_name,
                "needs_refill_for": p.needs_refill_for,
                "refill_due_date": str(p.refill_due_date)
            }
            for p in patients if p.refill_trigger
        ]

        inventory = [
            {
                "name": m.name,
                "stock_quantity": m.stock_quantity,
                "requires_prescription": m.requires_prescription,
                "expiry_date": m.expiry_date
            }
            for m in medicines
        ]

        return {
            "stats": {"total_medicines": total_meds, "low_stock": low_stock, "out_of_stock": out_of_stock},
            "refills": refills,
            "inventory": inventory
        }

# --- 6. 7-DAY AUTOMATED REMINDER ROUTE (DEMO OVERRIDE) ---
@app.post("/api/send_weekly_reminders")
async def send_weekly_reminders():
    """Triggers communication for patients needing refills (Terminal print demo)."""
    with Session(engine) as session:
        # Bypassing strict dates for demo: just grabbing 4 patients who need refills
        patients_to_warn = session.exec(
            select(Patient).where(Patient.refill_trigger == True).limit(4)
        ).all()
        
        notified_count = 0
        print("\n" + "="*50)
        print("🚀 INITIATING AI OUTREACH PROTOCOL")
        print("="*50)
        for p in patients_to_warn:
            print(f"📧 [SENT TO aryanbhandari621@gmail.com]: {p.patient_name}, your {p.needs_refill_for} runs out soon. Reply to your Copilot to refill.")
            notified_count += 1
        print("="*50 + "\n")
            
        return {"status": "success", "message": f"Successfully blasted {notified_count} AI reminders to critical patients."}

# --- 7. HISTORICAL PREDICTIVE SCAN ROUTE ---
@app.get("/api/predict")
async def run_predictive_scan():
    predict_task = Task(
        description=(
            "Use the analyze_historical_demand tool to scan the SQLite database. "
            "Write a short, highly professional 'Historical Supply Chain Alert' report. "
            "Identify which items are burning the fastest and exactly how many we need to reorder to survive the next 30 days. "
            "Format with clear HTML bullet points."
        ),
        expected_output="An HTML report of historical burn rates and reorder recommendations.",
        agent=proactive_agent
    )
    crew = Crew(agents=[proactive_agent], tasks=[predict_task], verbose=True)
    report = crew.kickoff()
    return {"report": str(report)}

# --- 8. LIVE ENVIRONMENTAL ALERTS ROUTE ---
@app.get("/api/environmental_alerts")
async def run_environmental_scan():
    env_task = Task(
        description=(
            "Execute the fetch_live_environmental_threats tool. "
            "Write an 'Emergency Environmental & Outbreak Alert Report'. "
            "Section 1: The current live weather and AQI analysis. "
            "Section 2: Active local health threats and virus outbreaks. "
            "Section 3: EXACT emergency medicines the pharmacy needs to order right now to prepare the community for these specific live threats. "
            "Format with clear HTML bullet points and bold text."
        ),
        expected_output="An HTML report predicting medical demand based on live weather and news.",
        agent=environmental_agent
    )
    crew = Crew(agents=[environmental_agent], tasks=[env_task], verbose=True)
    report = crew.kickoff()
    return {"report": str(report)}

# --- 9. AUTOMATED BACKGROUND TASK (REAL EMAIL DEMO MODE) ---
async def automated_3_day_reminder_loop():
    """Runs continuously in the background and fires real emails."""
    while True:
        try:
            with Session(engine) as session:
                # Grab 1 patient for the demo to avoid spamming yourself too much
                critical_patients = session.exec(
                    select(Patient).where(Patient.refill_trigger == True).limit(1)
                ).all()
                
                if critical_patients:
                    print("\n" + "*"*60)
                    print("⏳ [CRON-SYSTEM] FIRING REAL EMAIL VIA GMAIL SMTP...")
                    print("*"*60)
                    for p in critical_patients:
                        success = send_real_email(
                            recipient_email="prathamjain1410@gmail.com", 
                            patient_name=p.patient_name, 
                            medicine_name=p.needs_refill_for, 
                            due_date=str(p.refill_due_date)
                        )
                        if success:
                            print(f"✅ SUCCESSFULLY SENT REAL EMAIL TO prathamjain1410@gmail.com")
                    print("*"*60 + "\n")
        except Exception as e:
            print(f"Background task error: {e}")
        
        # Testing timer: runs every 60 seconds.
        # Once you verify it works, change `60` to `21600` for a 6-hour loop.
        await asyncio.sleep(60) 

@app.on_event("startup")
async def start_background_tasks():
    # This ignores the deprecation warning and safely starts your background loop
    asyncio.create_task(automated_3_day_reminder_loop())

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
