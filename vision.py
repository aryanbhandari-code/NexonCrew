import os
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv

# Force the file to read your .env variables
load_dotenv()

def verify_prescription_with_gemini(image_bytes):
    """Reads a prescription image and extracts the medical data."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "System Error: GEMINI_API_KEY is missing from the .env file."
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
        prompt = """
        You are a medical data extraction AI. Analyze this prescription image.
        Extract and format the response exactly like this:
        [VERIFIED PRESCRIPTION]
        Patient Name: <name>
        Prescribed Medicine: <medicine>
        Doctor Approved: Yes
        """
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"Error reading prescription: {str(e)}"