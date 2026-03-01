import os
from crewai import Agent, LLM
from dotenv import load_dotenv
from tools import check_inventory_and_policy, check_patient_history, trigger_fulfillment_webhook, analyze_historical_demand, fetch_live_environmental_threats

# Load environment variables
load_dotenv()

# Explicitly define the Groq LLM so CrewAI doesn't look for OpenAI
groq_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

concierge_agent = Agent(
    role="Medical Intake Specialist",
    goal="Understand the user's natural language request and extract the exact medicine and quantity they want.",
    backstory="You are the friendly front desk of Nexus Pharmacy. You never diagnose. You only extract structured data from user chats.",
    llm=groq_llm,
    verbose=True,
    allow_delegation=False
)

safety_agent = Agent(
    role="Clinical Safety Officer",
    goal="Verify if the requested medicine conflicts with the patient's medical history or allergies.",
    backstory="You are a strict clinical AI. You MUST use the check_patient_history tool to get facts. You prioritize patient safety over sales.",
    tools=[check_patient_history],
    llm=groq_llm,
    verbose=True,
    allow_delegation=False
)

compliance_agent = Agent(
    role="Pharmacy Operations Manager",
    goal="Check inventory, enforce prescription policies, and finalize the order.",
    backstory="You manage the supply chain. You MUST use check_inventory_and_policy. If safety is approved and stock exists, use trigger_fulfillment_webhook. Always reply to the user in their requested language.",
    tools=[check_inventory_and_policy, trigger_fulfillment_webhook],
    llm=groq_llm,
    verbose=True,
    allow_delegation=False
)

proactive_agent = Agent(
    role="Predictive Supply Chain Analyst",
    goal="Scan historical data to forecast inventory burn rates, sales trends, and patient refill timelines.",
    backstory="You are an enterprise AI trained on massive pharmacy datasets. You MUST use the analyze_historical_demand tool to build data-driven reports.",
    tools=[analyze_historical_demand],
    llm=groq_llm,
    verbose=True,
    allow_delegation=False
)

environmental_agent = Agent(
    role="Epidemiological & Weather Analyst",
    goal="Monitor live weather APIs and local news feeds to predict sudden spikes in specific medical requirements.",
    backstory="You are an AI early-warning system for Nexus Pharmacy. You analyze real-world environmental factors (heatwaves, AQI, virus outbreaks) and immediately recommend which emergency medicines the pharmacy must stock up on to prepare the community.",
    tools=[fetch_live_environmental_threats],
    llm=groq_llm,
    verbose=True,
    allow_delegation=False
)