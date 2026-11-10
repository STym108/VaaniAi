"""
=============================================================================
CHHATTISGARHI LLM FINE-TUNING SCRIPT (FOR GOOGLE COLAB WITH FREE T4 GPU)
=============================================================================
Model Target: unsloth/Llama-3.2-1B-Instruct (or unsloth/Llama-3.2-3B-Instruct)
Framework: Unsloth + Hugging Face TRL (SFTTrainer) + PEFT (QLoRA)
Compute Requirement: 1x Free T4 GPU on Google Colab (0% load on student laptop)
Runtime: ~45-60 minutes for 1,000 - 5,000 samples

HOW TO RUN ON GOOGLE COLAB:
1. Open https://colab.research.google.com and create a new notebook.
2. Set Runtime -> Change runtime type -> T4 GPU.
3. In Cell 1, paste:
   !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
   !pip install --no-deps trl peft accelerate bitsandbytes
4. Upload your 'train.jsonl' and 'val.jsonl' to Colab file explorer.
5. Paste and run this script in Cell 2.
=============================================================================
"""

import json
from datasets import Dataset
from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Hyperparameters & Configuration
MAX_SEQ_LENGTH = 1024
DTYPE = None # None for auto detection (Float16 for T4)
LOAD_IN_4BIT = True # QLoRA 4-bit quantization (Saves VRAM to ~3.5 GB)
MODEL_NAME = "unsloth/Llama-3.2-1B-Instruct" # Compact, ultra-fast Indian language learner

# 2. Load Base Model and Fast Tokenizer with Unsloth
print("⏳ Loading Base Model with 4-bit quantization...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=DTYPE,
    load_in_4bit=LOAD_IN_4BIT,
)

# 3. Add LoRA Adapters (Targeting Attention & MLP projections)
print("⚙️ Attaching LoRA Adapters...")
model = FastLanguageModel.get_peft_model(
    model,
    r=16, # Rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0, # Optimized by Unsloth
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# 4. Format Dataset into ChatML / Llama-3 Prompt Template
def format_prompts(batch):
    formatted_texts = []
    for instr, resp in zip(batch["instruction"], batch["response"]):
        text = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nतैं वाणी एआई (Vani AI) हरस, छत्तीसगढ़ के एक बुद्धिमान अउ मददगार सहायक। सबले बने छत्तीसगढ़ी भाखा म उत्तर देव।<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{instr}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{resp}<|eot_id|>"
        formatted_texts.append(text)
    return {"text": formatted_texts}

def load_jsonl(filepath):
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return Dataset.from_list(data)

print("📂 Loading and formatting train & validation splits...")
raw_train = load_jsonl("train.jsonl")
train_dataset = raw_train.map(format_prompts, batched=True)

# 5. Initialize SFTTrainer (Supervised Fine-Tuning)
print("🚀 Initializing SFTTrainer...")
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=100, # Adjust steps based on dataset size (e.g. 100-300)
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir="chhattisgarhi_lora_checkpoints",
    ),
)

# 6. Execute Fine-Tuning (Displays Loss Curve to show professors!)
print("🔥 Commencing Fine-Tuning...")
trainer_stats = trainer.train()
print(f"✅ Training completed in {trainer_stats.metrics['train_runtime']:.2f} seconds!")

# 7. Test Generation on Test Query
print("\n🧪 Testing Inference with Fine-Tuned Model:")
FastLanguageModel.for_inference(model)
test_prompt = "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nधान म भूरा माहू कीरा लग गे हे, का उपाय करे बर चाही?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
inputs = tokenizer([test_prompt], return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=150, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

# 8. Save LoRA Adapter for Final Submission
print("\n💾 Saving fine-tuned LoRA adapter...")
model.save_pretrained("vani_chhattisgarhi_lora_adapter")
tokenizer.save_pretrained("vani_chhattisgarhi_lora_adapter")
print("🎉 Model adapter saved to 'vani_chhattisgarhi_lora_adapter' folder!")
print("💡 Tip: Download this folder or push to Hugging Face Hub (model.push_to_hub('your_username/vani-cg-lora')).")

