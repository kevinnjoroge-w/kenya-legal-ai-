"""
Kenya Legal AI — Fine-tuning Data Prep
======================================
Converts processed Qdrant document chunks (all_documents.jsonl) into a format 
suitable for LLM fine-tuning (e.g., OpenAI or HuggingFace JSONL format).
"""

import json
import logging
from pathlib import Path
import random
from src.config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_qa_pairs(chunk: dict) -> list[dict]:
    """Generate hypothetical Q&A pairs based on a text chunk."""
    pairs = []
    text = chunk.get("text", "")
    title = chunk.get("document_title", "a legal document")
    doc_type = chunk.get("document_type", "document")
    section = chunk.get("section", "")
    
    if not text or len(text) < 100:
        return pairs

    # Prompt 1: Explain the section
    question1 = f"What does {section} of {title} say?" if section else f"What are the provisions of {title} regarding this topic?"
    answer1 = f"According to {title}{', ' + section if section else ''}:\n\n{text}"
    
    pairs.append({
        "messages": [
            {"role": "system", "content": "You are a senior Kenyan advocate with 20 years of experience. Answer directly and cite the law."},
            {"role": "user", "content": question1},
            {"role": "assistant", "content": answer1}
        ]
    })
    
    # Prompt 2: Contextual application (more organic questions)
    if doc_type == "judgment":
        question2 = f"Can you summarize the findings in {title}?"
        answer2 = f"In the case of {title}, the court stated:\n\n{text}"
    elif doc_type == "act" or doc_type == "constitution":
        question2 = f"Under Kenyan law, specifically {title}, what is the rule here?"
        answer2 = f"Under {title}{', ' + section if section else ''}, the rule is as follows:\n\n{text}"
    else:
        question2 = f"What is the legal position in {title}?"
        answer2 = f"The legal position as stated in {title} is:\n\n{text}"

    pairs.append({
        "messages": [
            {"role": "system", "content": "You are a senior Kenyan advocate with 20 years of experience. Answer directly and cite the law."},
            {"role": "user", "content": question2},
            {"role": "assistant", "content": answer2}
        ]
    })
    
    return pairs

def prepare_finetuning_data():
    settings = get_settings()
    input_file = Path(settings.processed_data_dir) / "all_documents.jsonl"
    output_file = Path(settings.processed_data_dir) / "finetuning_dataset.jsonl"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return

    logger.info(f"Reading processed chunks from {input_file}")
    
    dataset = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                chunk = json.loads(line)
                dataset.extend(generate_qa_pairs(chunk))
            except json.JSONDecodeError:
                continue
                
    # Shuffle the dataset to ensure a good mix of document types
    random.seed(42)
    random.shuffle(dataset)
    
    # Save the dataset
    logger.info(f"Writing {len(dataset)} training examples to {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    logger.info("Done! You can now use finetuning_dataset.jsonl to train your model.")

if __name__ == "__main__":
    prepare_finetuning_data()
