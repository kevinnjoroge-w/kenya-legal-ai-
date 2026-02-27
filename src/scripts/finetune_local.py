"""
Kenya Legal AI — Local Fine-Tuning Script
=========================================
Fine-tunes Llama-3 locally using Unsloth.
This script assumes you have an NVIDIA GPU and Unsloth installed.
"""

import os
import torch
import logging
from pathlib import Path
from datasets import load_dataset
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from trl import SFTTrainer
from transformers import TrainingArguments
from src.config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = get_settings()
    data_path = Path(settings.processed_data_dir) / "finetuning_dataset.jsonl"
    
    if not data_path.exists():
        logger.error(f"Training data not found at {data_path}")
        logger.error("Run `python src/scripts/prepare_finetuning_data.py` first.")
        return

    logger.info("Initializing Unsloth FastLanguageModel...")
    max_seq_length = 2048
    dtype = None # Auto-detects bf16/fp16
    load_in_4bit = True # Use 4-bit quantization to fit on most GPUs (e.g., RTX 3060/4060)

    # Load 4-bit quantized Llama-3.1-8B
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Meta-Llama-3.1-8B-Instruct",
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )

    # Set up LoRA Adapters (trains only a small percentage of weights)
    logger.info("Setting up PEFT / LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16, 
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0, 
        bias="none",    
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )

    # Setup Chat Template
    logger.info("Applying Llama-3 Chat Template...")
    tokenizer = get_chat_template(
        tokenizer,
        chat_template="llama-3",
        mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"}
    )

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
        return { "text": texts }

    # Load dataset
    logger.info(f"Loading dataset from {data_path}")
    dataset = load_dataset("json", data_files=str(data_path), split="train")
    dataset = dataset.map(formatting_prompts_func, batched=True)

    # Start Training
    logger.info("Starting SFTTrainer...")
    output_dir = "models/kenya-legal-llama-3"
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=60, # Change this to a larger number (e.g. 500) for a full fine-tune
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=output_dir,
        ),
    )

    trainer.train()

    logger.info(f"Training complete! Model saved to {output_dir}")
    
    # Save the adapter
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    logger.info("If you want to export to GGUF for Ollama, you can uncomment the GGUF export lines in the script.")
    # Export to GGUF (Uncomment these lines to export for Ollama)
    # logger.info("Exporting to GGUF format...")
    # model.save_pretrained_gguf(f"{output_dir}_gguf", tokenizer, quantization_method="q4_k_m")
    # logger.info("GGUF Export complete!")

if __name__ == "__main__":
    main()
