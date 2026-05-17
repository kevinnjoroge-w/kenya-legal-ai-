import os
import json
import random
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from groq import AsyncGroq

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in .env")

# Initialize async Groq client for super fast generation
client = AsyncGroq(api_key=GROQ_API_KEY)

PROMPT_TEMPLATE = """You are an elite legal analyst. I will provide you with a raw chunk of a Kenyan legal case or document.
Your task is to break it down into a short, highly precise, and insightful analysis.

Follow this EXACT format:
**Facts**: [2-3 sentences summarizing the core events/dispute]
**Legal Concepts**: [Comma-separated list of the primary legal doctrines involved]
**Analysis**: [A sharp, concise breakdown of the judge's reasoning or the legal implications]
**Potential Biases/Nuances**: [Identify any judicial biases, societal context, or legal ambiguities present]

Do NOT add any filler words like "Here is the analysis". Just output the format.

RAW DOCUMENT:
{document}
"""

async def generate_analysis(chunk_text: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        try:
            chat_completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert Kenyan legal analyst."},
                    {"role": "user", "content": PROMPT_TEMPLATE.format(document=chunk_text)}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=500,
            )
            
            assistant_response = chat_completion.choices[0].message.content
            
            # Format as expected by finetune_local.py
            return {
                "messages": [
                    {
                        "role": "user", 
                        "content": f"Provide an in-depth breakdown of the following legal text, including facts, concepts, analysis, and biases:\n\n{chunk_text}"
                    },
                    {
                        "role": "assistant", 
                        "content": assistant_response.strip()
                    }
                ]
            }
        except Exception as e:
            print(f"Error generating analysis: {e}")
            return None

async def main():
    docs_path = Path("data/processed/all_documents.jsonl")
    out_path = Path("data/processed/finetune_dataset.jsonl")
    
    print("Loading documents...")
    all_chunks = []
    with open(docs_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            # Only take substantial chunks to ensure good analysis
            if len(data.get("content", "")) > 1000:
                all_chunks.append(data["content"])
                
    print(f"Found {len(all_chunks)} valid chunks. Selecting 300 random chunks for dataset...")
    random.seed(42) # For reproducibility
    selected_chunks = random.sample(all_chunks, min(300, len(all_chunks)))
    
    print("Sending to Groq to generate synthetic fine-tuning dataset...")
    # Use a semaphore to avoid hitting Groq rate limits (adjust if needed)
    sem = asyncio.Semaphore(10)
    
    tasks = [generate_analysis(chunk, sem) for chunk in selected_chunks]
    results = await asyncio.gather(*tasks)
    
    valid_results = [r for r in results if r is not None]
    
    print(f"Successfully generated {len(valid_results)} training examples!")
    print(f"Saving to {out_path}...")
    
    with open(out_path, "w", encoding="utf-8") as f:
        for res in valid_results:
            f.write(json.dumps(res) + "\n")
            
    print("Done! You can now run finetune_local.py on this dataset.")

if __name__ == "__main__":
    asyncio.run(main())
