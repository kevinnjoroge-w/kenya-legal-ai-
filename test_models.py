import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API key loaded: {'Yes' if api_key else 'No'}")
genai.configure(api_key=api_key)

print("Available models:")
try:
    models = list(genai.list_models())
    if not models:
        print("No models found!")
    for m in models:
        print(f"Model: {m.name}")
        print(f"  Supported methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")
