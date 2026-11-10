import os
import sys
import json
import time
import random
import argparse
from pathlib import Path

# Add project root and backend directory to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from config import GEMINI_API_KEY
from dataset_pipeline.topics import TAXONOMY, LINGUISTIC_PROMPT_GUIDELINES

OUTPUT_FILE = Path(__file__).resolve().parent / "chhattisgarhi_instruct_dataset.jsonl"

# Read API keys safely from environment variables (never hardcoded for GitHub)
env_pool = os.getenv("GEMINI_API_KEYS_POOL", "")
API_KEYS_POOL = [k.strip() for k in env_pool.split(",") if k.strip()]
if GEMINI_API_KEY and GEMINI_API_KEY not in API_KEYS_POOL:
    API_KEYS_POOL.insert(0, GEMINI_API_KEY)

class KeyRotator:
    def __init__(self, keys):
        from google import genai
        self.keys = keys
        self.clients = [genai.Client(api_key=k) for k in keys]
        self.current_idx = 0
        self.exhausted = set()

    def get_client(self):
        if len(self.exhausted) >= len(self.clients):
            return None, None
        while self.current_idx in self.exhausted:
            self.current_idx = (self.current_idx + 1) % len(self.clients)
        return self.clients[self.current_idx], self.current_idx

    def mark_exhausted(self, idx):
        self.exhausted.add(idx)
        print(f"   ⚠️ Key #{idx+1} ({self.keys[idx][:10]}...) quota exhausted. Rotating to next key...")
        self.current_idx = (self.current_idx + 1) % len(self.clients)

    def rotate_next(self):
        self.current_idx = (self.current_idx + 1) % len(self.clients)

def load_existing_instructions(filepath: Path) -> set:
    """Loads already generated instructions to prevent duplicate questions."""
    existing = set()
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        existing.add(data.get("instruction", "").strip())
                    except Exception:
                        pass
    return existing

def generate_batch(rotator: KeyRotator, domain: str, topic: str, count: int = 5) -> list:
    """Generates a batch of diverse Chhattisgarhi QA pairs with key rotation."""
    from google.genai import types

    user_prompt = f"""
Domain: {domain}
Specific Topic: {topic}

Task:
Generate {count} completely unique, practical, and culturally authentic instruction-response pairs in Chhattisgarhi language (Devanagari script).

Requirements:
1. Every 'instruction' must represent a realistic question a native Chhattisgarhi speaker would ask (using words like काबर, कइसे, कतेक, का, आदि).
2. Every 'response' must be a detailed, helpful, respectful answer (3-5 sentences) in pure Chhattisgarhi explaining the solution clearly.
3. Diverse persona styles:
   - A farmer asking practical advice
   - A student asking about exams or culture
   - A rural homemaker or elder asking about schemes/health
   - A general citizen asking about traditions

Return STRICTLY a valid JSON array of objects with keys "instruction" and "response".
Do not include markdown code fence formatting (no ```json).

Example format:
[
  {{
    "instruction": "धान म तना छेदक कीरा लग गे हे, एकर रोकथाम बर का करना चाही?",
    "response": "धान म तना छेदक लगे म सबले पहिली नीम के तेल के 5 मिली प्रति लीटर पानी म घोल बना के छिड़काव करव। अगर कीरा जादा बढ़ गे हे, त करटाप हाइड्रोक्लोराइड 4G दानेदार दवाई ला 10 किलो प्रति एकड़ के हिसाब से खेत म डालव। खेत के पानी ला दू दिन बर निकाल देव ताकि दवाई के पूरा असर होवय।"
  }}
]
"""

    models_to_try = ["gemini-3.6-flash", "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash"]

    max_key_attempts = len(rotator.clients)
    attempts = 0

    while attempts < max_key_attempts:
        client, key_idx = rotator.get_client()
        if client is None:
            print("\n🛑 ALL API Keys in the pool have exceeded their daily quota.")
            return []

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=LINGUISTIC_PROMPT_GUIDELINES,
                        temperature=0.75,
                        response_mime_type="application/json"
                    )
                )
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                data = json.loads(raw_text.strip())
                # Rotate key slightly to distribute load evenly
                rotator.rotate_next()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "pairs" in data:
                    return data["pairs"]
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    rotator.mark_exhausted(key_idx)
                    break # Break inner model loop, try next key
                time.sleep(1)
                continue
        attempts += 1

    return []

def run_pipeline(target_count: int = 500, batch_size: int = 5):
    print(f"🚀 Initializing Chhattisgarhi Dataset Generation Pipeline (Multi-Key Pool)...")
    print(f"🎯 Target samples: {target_count}")
    print(f"📂 Output destination: {OUTPUT_FILE}")
    print(f"🔑 Active API Keys in pool: {len(API_KEYS_POOL)}")

    rotator = KeyRotator(API_KEYS_POOL)
    existing_instructions = load_existing_instructions(OUTPUT_FILE)
    print(f"📊 Existing unique samples found on disk: {len(existing_instructions)}")

    current_count = len(existing_instructions)
    if current_count >= target_count:
        print(f"✅ Already reached target {target_count} samples!")
        return

    domains = list(TAXONOMY.keys())
    saved_in_this_run = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as out_f:
        while current_count < target_count:
            domain = random.choice(domains)
            topic = random.choice(TAXONOMY[domain])

            print(f"\n🔄 [{current_count + 1}/{target_count}] Generating for [{domain}] -> '{topic[:40]}...'")
            try:
                pairs = generate_batch(rotator, domain=domain, topic=topic, count=batch_size)
                if not pairs:
                    client, _ = rotator.get_client()
                    if client is None:
                        print(f"\n🛑 All keys exhausted. Halting safely at {current_count} samples.")
                        break

                valid_batch_count = 0
                for pair in pairs:
                    instr = pair.get("instruction", "").strip()
                    resp = pair.get("response", "").strip()

                    if not instr or not resp:
                        continue
                    if len(instr) < 10 or len(resp) < 25:
                        continue
                    if instr in existing_instructions:
                        continue

                    sample = {
                        "id": f"cg_{domain[:4]}_{current_count + 1:05d}",
                        "domain": domain,
                        "topic": topic,
                        "instruction": instr,
                        "response": resp,
                        "source": "vani_cg_curated_v1"
                    }

                    out_f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                    out_f.flush()

                    existing_instructions.add(instr)
                    current_count += 1
                    saved_in_this_run += 1
                    valid_batch_count += 1

                    if current_count >= target_count:
                        break

                print(f"   ✨ Added {valid_batch_count} new pairs. Total dataset: {current_count}/{target_count}")
                time.sleep(1.2)

            except Exception as e:
                print(f"   ⚠️ Error during batch: {e}. Cooling down...")
                time.sleep(3)

    print(f"\n🎉 Pipeline run completed! Added {saved_in_this_run} pairs. Total now: {current_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chhattisgarhi Dataset Generator")
    parser.add_argument("--count", type=int, default=500, help="Target total samples")
    parser.add_argument("--batch", type=int, default=5, help="Samples per LLM generation call")
    args = parser.parse_args()

    run_pipeline(target_count=args.count, batch_size=args.batch)
