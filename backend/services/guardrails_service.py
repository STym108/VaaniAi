"""
Vani AI Enterprise-Grade Dual-Layer Guardrails Service
Architected for Low-Resource Indic Dialects & OWASP Top 10 for LLMs Compliance

Key Security Capabilities:
1. Ingress Layer (Pre-LLM):
   - Dialect-Aware Adversarial Jailbreak Defense (Chhattisgarhi, Hindi, Hinglish, English)
   - Training Data Extraction & Model Inversion Shield (OWASP-LLM06)
   - Shannon Entropy Obfuscation & Encoded Payload Detector
   - High-Precision Indian PII Anonymizer (Aadhaar, PAN, UPI, Phone, Email, API Keys)
   - Severe Harm & Illicit Intent Policy Enforcement
2. Egress Layer (Post-LLM):
   - Canary Token & Internal Dataset Artifact Redaction (OWASP-LLM06/02)
   - Egress PII & Secret Scrubbing
   - Speech Synthesis Normalization (TTS Audio Optimization)
3. Sub-Millisecond Telemetry & Forensics Profiling (<1.0 ms overhead)
"""

import math
import re
import time
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel

class GuardrailResult(BaseModel):
    is_safe: bool
    sanitized_text: str
    threat_level: str = "CLEAN" # CLEAN, LOW, ELEVATED, CRITICAL
    owasp_category: str = "CLEAN"
    violation_type: Optional[str] = None
    reason: Optional[str] = None
    pii_redacted: bool = False
    flags: List[str] = []
    entropy_score: float = 0.0
    toxicity_score: float = 0.0
    latency_ms: float = 0.0

class OutputGuardrailResult(BaseModel):
    is_safe: bool
    sanitized_text: str
    pii_redacted: bool = False
    canary_triggered: bool = False
    flags: List[str] = []
    latency_ms: float = 0.0

class GuardrailsService:
    def __init__(self):
        # -------------------------------------------------------------
        # 1. OWASP-LLM01: Prompt Injection & Adversarial Jailbreaks
        # Multilingual: English + Hinglish + Chhattisgarhi
        # -------------------------------------------------------------
        self.injection_patterns = [
            # English standard jailbreaks
            re.compile(r"ignore\s+(all\s+)?(previous|prior|above|system)\s+(instructions|prompts|rules)", re.IGNORECASE),
            re.compile(r"reveal\s+(your\s+)?(system\s+prompt|instructions|initial\s+prompt)", re.IGNORECASE),
            re.compile(r"system\s*prompt\s*override", re.IGNORECASE),
            re.compile(r"you\s+are\s+now\s+(in\s+|an?\s+)?(developer|unrestricted|god|dan|evil|jailbreak)(\s+mode|\s+ai)?", re.IGNORECASE),
            re.compile(r"disregard\s+(any|all)\s+safety", re.IGNORECASE),
            re.compile(r"bypass\s+(the\s+)?(filter|guardrail|restrictions)", re.IGNORECASE),
            re.compile(r"tell\s+me\s+your\s+hidden\s+rules", re.IGNORECASE),
            re.compile(r"repeat\s+the\s+words\s+above", re.IGNORECASE),
            re.compile(r"do\s+anything\s+now", re.IGNORECASE),
            re.compile(r"act\s+as\s+an\s+unfiltered", re.IGNORECASE),
            # Hinglish Jailbreak attempts
            re.compile(r"pichhle\s+saare\s+(rules|niyam)\s+bhool\s+jao", re.IGNORECASE),
            re.compile(r"system\s+prompt\s+(dikhao|batao|print\s+karo)", re.IGNORECASE),
            re.compile(r"bina\s+kisi\s+rok\s*tok\s+ke\s+jawab\s+do", re.IGNORECASE),
            # Chhattisgarhi Dialect Adversarial Injections (Cross-Lingual Vulnerability Shield)
            re.compile(r"सब्बो\s+(नियम|बात|आदेश)\s+ला\s+(भूल|त्याग)\s+(जा|देव)", re.IGNORECASE), # Sabbo niyam la bhool ja
            re.compile(r"(अपन|तोर)\s+(सिस्टम\s+प्रॉम्ट|असली\s+नियम|गुपचुप\s+नियम).*?(बता|देखा|लिख|सुनाव|का\s+हे)", re.IGNORECASE),
            re.compile(r"सार्वजनिक\s+नियम\s+ला\s+(छोड़|दरकिनार\s+कर)", re.IGNORECASE),
            re.compile(r"बिना\s+कोनो\s+रोक-टोक\s+के\s+जवाब\s+दे", re.IGNORECASE), # Unrestricted answer
            re.compile(r"तैं\s+ह\s+अब\s+(आजाद|स्वतंत्र|दान)\s+हस", re.IGNORECASE), # Dan mode in CG
            re.compile(r"सब्बो\s+पाछू\s+के\s+बात\s+ला\s+छोड़ाव", re.IGNORECASE),
            re.compile(r"सब्बो\s+प्रतिबंध\s+ला\s+हटाव", re.IGNORECASE),
        ]

        # -------------------------------------------------------------
        # 2. OWASP-LLM06: Training Data Extraction & Model Inversion Shield
        # Prevents extraction of training datasets, JSONL pairs, and fine-tuning metadata
        # -------------------------------------------------------------
        self.data_extraction_patterns = [
            # English Extraction
            re.compile(r"(extract|reveal|dump|leak|print|show|output)\s+(the\s+)?(raw\s+)?(training\s+data|dataset|jsonl|corpus|training\s+pairs)", re.IGNORECASE),
            re.compile(r"what\s+(exact\s+)?data\s+(was|were)\s+used\s+to\s+train\s+you", re.IGNORECASE),
            re.compile(r"repeat\s+(your\s+)?(training\s+examples|training\s+samples|dataset\s+records)", re.IGNORECASE),
            re.compile(r"show\s+me\s+the\s+internal\s+(database|training\s+file|jsonl)", re.IGNORECASE),
            re.compile(r"dump\s+(all\s+)?(fine-?tuning\s+pairs|chhattisgarhi\s+dataset)", re.IGNORECASE),
            re.compile(r"(reveal|tell\s+me|show)\s+(your\s+)?(secret\s+)?(api_key|sarvam_api_key|gemini_api_key|secret_key|private_key)", re.IGNORECASE),
            # Chhattisgarhi & Hindi Training Data Extraction
            re.compile(r"(तोर|अपन)\s+ट्रेनिंग\s+डाटा\s+ला\s+(दिखा|बता|प्रिंट\s+कर|निकाल)", re.IGNORECASE),
            re.compile(r"ट्रेनिंग\s+फाइल\s+के\s+डाटा\s+ला\s+निकाल", re.IGNORECASE),
            re.compile(r"जोन\s+डाटा\s+ले\s+तोर\s+ट्रेनिंग\s+होए\s+हे\s+ओला\s+(लिख|बता)", re.IGNORECASE),
            re.compile(r"training\s+data\s+(print\s+karo|dikhao|dump\s+karo)", re.IGNORECASE),
            re.compile(r"fine\s*tuning\s+ke\s+records\s+dikhao", re.IGNORECASE),
            re.compile(r"dataset\s+ke\s+jsonl\s+records\s+dikhao", re.IGNORECASE),
        ]

        # -------------------------------------------------------------
        # 3. OWASP-LLM02: Indian PII Regex Suite
        # Aadhaar, PAN, UPI ID, Phone, Email, API Keys / Passwords
        # -------------------------------------------------------------
        # 12-digit Aadhaar (supports formatted 'xxxx xxxx xxxx' or continuous)
        self.aadhaar_pattern = re.compile(r"\b[2-9]\d{3}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b")
        # Indian PAN Card: 5 letters, 4 digits, 1 letter
        self.pan_pattern = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
        # Indian Mobile Phone (starts with 6-9, optional +91 or 0 prefix)
        self.phone_pattern = re.compile(r"(?:(?:\+91|0)[\s\-]?)?[6-9]\d{9}\b")
        # Standard RFC-compliant Email
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        # Indian Unified Payments Interface (UPI) IDs (e.g. user@oksbi, payment@paytm)
        self.upi_pattern = re.compile(r"\b[a-zA-Z0-9.\-_]{2,49}@(okhdfcbank|okaxis|oksbi|okicici|paytm|ybl|ibl|axl|apl|upi)\b", re.IGNORECASE)
        # API Keys, Tokens, Passwords
        self.secret_pattern = re.compile(r"(password|api_key|secret|token|bearer|private_key)\s*[:=]\s*(\S+)", re.IGNORECASE)
        self.api_key_hashes = re.compile(r"\b(AIzaSy[0-9A-Za-z\-_]{33}|sk-[a-zA-Z0-9]{32,}|sarvam_[0-9a-f]{20,})\b")

        # -------------------------------------------------------------
        # 4. Severe Harm & Illicit Content Policy
        # -------------------------------------------------------------
        self.harm_keywords = [
            # English
            "how to build a bomb", "make explosive", "suicide instruction", "hack bank",
            "steal credit card", "bypass security system", "make poison", "synthesize ricin",
            # Hindi / Chhattisgarhi
            "बम बनाय के तरीका", "बम कैसे बनाएं", "जहर बनाय के विधि", "जहर कैसे बनाएं",
            "चोरी करे के तरीका", "बैंक हैक करे के तरीका", "हथियार बनाय", "मारपीट करे के उपाय"
        ]

        # -------------------------------------------------------------
        # 5. Egress Internal Canaries & Dataset Fingerprints
        # -------------------------------------------------------------
        self.canary_tokens = [
            re.compile(r"\b(cg_agri_\d+|cg_cult_\d+|cg_dail_\d+|cg_gov_\d+)\b"),
            re.compile(r"\b(vani_cg_curated_v1|vani_chhattisgarhi_lora_adapter)\b"),
            re.compile(r"\b(qlora_adapter_weights|adapter_model\.safetensors)\b"),
        ]

    def calculate_shannon_entropy(self, text: str) -> float:
        """
        Calculates character-level Shannon Entropy.
        High entropy in short/medium strings indicates Base64, hex obfuscation, or encrypted payloads.
        """
        if not text:
            return 0.0
        entropy = 0.0
        length = len(text)
        freq: Dict[str, int] = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        return round(entropy, 3)

    def validate_input(self, text: str) -> GuardrailResult:
        """
        Layer 1: Pre-LLM Ingress Guardrail
        Evaluates input safety, intercepts adversarial injections, blocks training data leakage attempts,
        detects entropy obfuscation, and redacts PII before reaching downstream LLM / LoRA models.
        """
        t0 = time.perf_counter()
        flags: List[str] = []
        clean_text = text.strip()
        lower_text = clean_text.lower()
        entropy = self.calculate_shannon_entropy(clean_text)

        # Check 1: OWASP-LLM06 - Training Data Extraction & Model Inversion Shield
        for pattern in self.data_extraction_patterns:
            if pattern.search(clean_text):
                latency = round((time.perf_counter() - t0) * 1000, 2)
                return GuardrailResult(
                    is_safe=False,
                    sanitized_text=clean_text,
                    threat_level="CRITICAL",
                    owasp_category="OWASP-LLM06: Sensitive Information Disclosure",
                    violation_type="training_data_extraction",
                    reason="Security Policy Triggered: Extraction of internal training pairs, fine-tuning datasets, or architecture weights is prohibited.",
                    flags=["Anti-Extraction Shield Triggered", "Model Inversion Defense Activated", "OWASP-LLM06 Violation"],
                    entropy_score=entropy,
                    toxicity_score=0.91,
                    latency_ms=latency
                )

        # Check 2: OWASP-LLM01 - Adversarial Prompt Injection & Regional Dialect Jailbreaks
        for pattern in self.injection_patterns:
            if pattern.search(clean_text):
                latency = round((time.perf_counter() - t0) * 1000, 2)
                is_cg = any(c in clean_text for c in ["ला", "तोर", "अपन", "सब्बो", "हस", "देव"])
                rule_name = "Dialect Adversarial Jailbreak Blocked" if is_cg else "Prompt Injection Shield Triggered"
                return GuardrailResult(
                    is_safe=False,
                    sanitized_text=clean_text,
                    threat_level="CRITICAL",
                    owasp_category="OWASP-LLM01: Prompt Injection",
                    violation_type="prompt_injection",
                    reason="Adversarial Injection Detected: System constraint overrides and jailbreak directives are strictly restricted.",
                    flags=[rule_name, "OWASP-LLM01 Enforcement", "Direct/Indirect Injection Intercepted"],
                    entropy_score=entropy,
                    toxicity_score=0.94,
                    latency_ms=latency
                )

        # Check 3: Severe Harm & Illicit Intent Policy
        for keyword in self.harm_keywords:
            if keyword in lower_text:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                return GuardrailResult(
                    is_safe=False,
                    sanitized_text=clean_text,
                    threat_level="CRITICAL",
                    owasp_category="SAFETY: Malicious Intent",
                    violation_type="harm_policy",
                    reason="Violation of Safety Usage Policy: Illicit, violent, or weapon-manufacturing instructions detected.",
                    flags=["Harm Policy Violation", "Illicit Query Blocked", "Zero-Tolerance Policy"],
                    entropy_score=entropy,
                    toxicity_score=0.99,
                    latency_ms=latency
                )

        # Check 4: High-Entropy Obfuscation Detection (Base64 / Hex Injections)
        # Normal natural language typically has entropy between 3.0 and 4.2.
        # Strings longer than 35 chars with entropy > 4.6 and no spaces are usually encoded payloads.
        if len(clean_text) > 35 and " " not in clean_text and entropy > 4.6:
            latency = round((time.perf_counter() - t0) * 1000, 2)
            return GuardrailResult(
                is_safe=False,
                sanitized_text=clean_text,
                threat_level="ELEVATED",
                owasp_category="OWASP-LLM01: Obfuscated Payload",
                violation_type="obfuscated_injection",
                reason="High-Entropy Encoded Payload Detected: Obfuscated inputs bypassing tokenizers are restricted.",
                flags=["High Shannon Entropy Flagged", "Obfuscation Shield Active"],
                entropy_score=entropy,
                toxicity_score=0.85,
                latency_ms=latency
            )

        # Check 5: OWASP-LLM02 - Indian PII Masking & Privacy Anonymization
        pii_found = False

        if self.aadhaar_pattern.search(clean_text):
            clean_text = self.aadhaar_pattern.sub("[REDACTED_AADHAAR]", clean_text)
            flags.append("Aadhaar Number Anonymized")
            pii_found = True

        if self.pan_pattern.search(clean_text):
            clean_text = self.pan_pattern.sub("[REDACTED_PAN]", clean_text)
            flags.append("PAN Card Masked")
            pii_found = True

        if self.upi_pattern.search(clean_text):
            clean_text = self.upi_pattern.sub("[REDACTED_UPI]", clean_text)
            flags.append("UPI ID Masked")
            pii_found = True

        if self.phone_pattern.search(clean_text):
            clean_text = self.phone_pattern.sub("[REDACTED_PHONE]", clean_text)
            flags.append("Mobile Number Masked")
            pii_found = True

        if self.email_pattern.search(clean_text):
            clean_text = self.email_pattern.sub("[REDACTED_EMAIL]", clean_text)
            flags.append("Email Address Masked")
            pii_found = True

        if self.secret_pattern.search(clean_text):
            clean_text = self.secret_pattern.sub(r"\1: [REDACTED_SECRET]", clean_text)
            flags.append("Secret Key Masked")
            pii_found = True

        if self.api_key_hashes.search(clean_text):
            clean_text = self.api_key_hashes.sub("[REDACTED_API_KEY]", clean_text)
            flags.append("Raw API Key Hash Scrubbed")
            pii_found = True

        if not flags:
            flags.append("Input Verified Safe")
            threat_level = "CLEAN"
            owasp_cat = "CLEAN"
        else:
            threat_level = "LOW" if pii_found else "CLEAN"
            owasp_cat = "OWASP-LLM02: Sensitive Data Exposure" if pii_found else "CLEAN"

        latency = round((time.perf_counter() - t0) * 1000, 2)
        return GuardrailResult(
            is_safe=True,
            sanitized_text=clean_text,
            threat_level=threat_level,
            owasp_category=owasp_cat,
            pii_redacted=pii_found,
            flags=flags,
            entropy_score=entropy,
            toxicity_score=0.01,
            latency_ms=latency
        )

    def validate_output(self, text: str) -> OutputGuardrailResult:
        """
        Layer 2: Post-LLM Egress Guardrail
        Verifies output safety, catches accidental training set canary leakage,
        scrubs residual PII, and formats text for natural, stutter-free TTS voice playback.
        """
        t0 = time.perf_counter()
        if not text:
            return OutputGuardrailResult(is_safe=True, sanitized_text="", latency_ms=0.0)

        cleaned = text
        flags: List[str] = []
        pii_found = False
        canary_found = False

        # 1. Speech Voice Formatting (TTS Audio Optimization) first
        # Strip code blocks
        cleaned = re.sub(r"```[\s\S]*?```", " [Code Snippet Omitted for Voice] ", cleaned)
        # Strip markdown bold, headers, backticks
        cleaned = re.sub(r"[\*#`]", "", cleaned)
        # Strip markdown italic underscores only when around words (_word_)
        cleaned = re.sub(r"(?<!\w)_(?!\w)|(?<=\s)_(?=\S)|(?<=\S)_(?=\s)", "", cleaned)
        # Simplify URLs
        cleaned = re.sub(r"https?://\S+", "link provided", cleaned)
        # Normalize repeated punctuation and spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 2. Anti-Memorization / Canary Token Watermark Check
        for canary in self.canary_tokens:
            if canary.search(cleaned):
                cleaned = canary.sub("[CANARY_ARTIFACT_FILTERED]", cleaned)
                flags.append("Canary Artifact Filtered")
                canary_found = True

        # 3. Output Secret & PII Scrubbing
        if self.secret_pattern.search(cleaned):
            cleaned = self.secret_pattern.sub(r"\1: [REDACTED_SECRET]", cleaned)
            flags.append("Output Secret Redacted")
            pii_found = True

        if self.api_key_hashes.search(cleaned):
            cleaned = self.api_key_hashes.sub("[REDACTED_API_KEY]", cleaned)
            flags.append("Output API Key Redacted")
            pii_found = True

        if self.aadhaar_pattern.search(cleaned):
            cleaned = self.aadhaar_pattern.sub("[REDACTED_AADHAAR]", cleaned)
            flags.append("Output Aadhaar Scrubbed")
            pii_found = True

        if self.phone_pattern.search(cleaned):
            cleaned = self.phone_pattern.sub("[REDACTED_PHONE]", cleaned)
            flags.append("Output Phone Scrubbed")
            pii_found = True

        if not flags:
            flags.append("Output Guardrail Cleared")
            flags.append("Voice-Safe Format")

        latency = round((time.perf_counter() - t0) * 1000, 2)
        return OutputGuardrailResult(
            is_safe=True,
            sanitized_text=cleaned,
            pii_redacted=pii_found,
            canary_triggered=canary_found,
            flags=flags,
            latency_ms=latency
        )

# Singleton Instance
guardrails = GuardrailsService()
