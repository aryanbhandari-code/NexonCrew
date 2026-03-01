import os
from dotenv import load_dotenv

def init_integrations():
    load_dotenv()
    required_keys = ["GROQ_API_KEY", "LANGCHAIN_API_KEY"]
    for key in required_keys:
        if not os.getenv(key):
            print(f"⚠️ Warning: {key} is missing in .env")
            
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "Nexus_Pharmacy_Demo")
    print("🚀 Integrations Initialized: LangSmith & Groq Ready.")