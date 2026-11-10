"""
Chhattisgarhi Dataset Validator, Statistics Profiler & Train/Val Splitter
Analyzes dataset quality, domain balance, dialectal authenticity, and splits data for training.
"""

import json
import random
from pathlib import Path
from collections import Counter

DATASET_FILE = Path(__file__).resolve().parent / "chhattisgarhi_instruct_dataset.jsonl"
TRAIN_FILE = Path(__file__).resolve().parent / "train.jsonl"
VAL_FILE = Path(__file__).resolve().parent / "val.jsonl"

CHHATTISGARHI_MARKERS = [
    "काबर", "कइसे", "कतेक", "कहाँ", "का", "हमन", "तुमन", "तोर", "मोर",
    "ओकर", "ओमन", "करत हे", "करत हन", "होवत हे", "नइ", "झन", "ला",
    "बर", "ददा", "दाई", "सियान", "मन", "भात", "खेत", "लइका", "गिस", "आइस"
]

def analyze_and_split(train_ratio: float = 0.9):
    if not DATASET_FILE.exists():
        print(f"❌ Dataset file not found at: {DATASET_FILE}")
        return

    samples = []
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    samples.append(data)
                except Exception as e:
                    print(f"⚠️ Error parsing line {idx}: {e}")

    total = len(samples)
    print("=" * 65)
    print(" 📊 CHHATTISGARHI INSTRUCTION DATASET AUDIT REPORT")
    print("=" * 65)
    print(f"Total Unique Verified Pairs: {total}")

    if total == 0:
        return

    # 1. Domain distribution
    domain_counts = Counter(s.get("domain", "unknown") for s in samples)
    print("\n[1] Domain Distribution:")
    for dom, count in domain_counts.items():
        pct = (count / total) * 100
        print(f"   • {dom:<25}: {count:>5} samples ({pct:.1f}%)")

    # 2. Length statistics
    instr_lens = [len(s.get("instruction", "").split()) for s in samples]
    resp_lens = [len(s.get("response", "").split()) for s in samples]

    avg_instr = sum(instr_lens) / total
    avg_resp = sum(resp_lens) / total

    print("\n[2] Length & Word-Count Metrics:")
    print(f"   • Avg Instruction Length : {avg_instr:.1f} words (Min: {min(instr_lens)}, Max: {max(instr_lens)})")
    print(f"   • Avg Response Length    : {avg_resp:.1f} words (Min: {min(resp_lens)}, Max: {max(resp_lens)})")

    # 3. Dialectal authenticity check
    marker_hits = Counter()
    for s in samples:
        text = s.get("instruction", "") + " " + s.get("response", "")
        for marker in CHHATTISGARHI_MARKERS:
            if marker in text:
                marker_hits[marker] += 1

    print("\n[3] Chhattisgarhi Dialectal Marker Frequency (Top 10):")
    for marker, freq in marker_hits.most_common(10):
        pct = (freq / total) * 100
        print(f"   • '{marker}': appears in {freq}/{total} samples ({pct:.1f}%)")

    # 4. Train / Validation Split
    random.seed(42)
    shuffled = samples.copy()
    random.shuffle(shuffled)

    split_idx = int(total * train_ratio)
    train_set = shuffled[:split_idx]
    val_set = shuffled[split_idx:]

    with open(TRAIN_FILE, "w", encoding="utf-8") as f:
        for s in train_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(VAL_FILE, "w", encoding="utf-8") as f:
        for s in val_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print("\n[4] Dataset Partitioning:")
    print(f"   • Train Split ({int(train_ratio*100)}%)     : {len(train_set)} samples -> {TRAIN_FILE.name}")
    print(f"   • Validation Split ({int((1-train_ratio)*100)}%): {len(val_set)} samples -> {VAL_FILE.name}")
    print("=" * 65)
    print("✅ Audit and train/val generation complete!")

if __name__ == "__main__":
    analyze_and_split()

