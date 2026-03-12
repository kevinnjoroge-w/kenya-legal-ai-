import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

try:
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content="Hello world",
        task_type="RETRIEVAL_DOCUMENT"
    )
    dim = len(result['embedding'])
    print(f"Dimension: {dim}")
except Exception as e:
    print(f"Error: {e}")
