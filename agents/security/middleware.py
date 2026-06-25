import re

class InjectionDetectedError(Exception):
    pass

ADVERSARIAL_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s+bypass",
    r"sudo\s+override",
    r"you\s+are\s+now",
    r"forget\s+your",
    r"disregard\s+(all|your)",
    r"new\s+persona",
]

PII_MASK_PATTERNS = {
    r"\$[\d,]+(\.\d{2})?":                              "[MASKED_CURRENCY]",
    r"\b[A-Z0-9]{20,}\b":                               "[MASKED_KEY]",
    r"(?i)(password|secret|api[_-]?key)\s*[:=]\s*\S+": "[MASKED_SECRET]",
}

def scan_ingest(prompt: str) -> str:
    for pattern in ADVERSARIAL_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise InjectionDetectedError(f"Adversarial pattern detected: {pattern}")
    for pattern, replacement in PII_MASK_PATTERNS.items():
        prompt = re.sub(pattern, replacement, prompt)
    return prompt
