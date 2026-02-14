import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\b(\+?\d{1,3}[\s-]?)?(\d[\s-]?){7,14}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

def redact_pii(text: str) -> str:
    if not text:
        return ""
    t = text
    t = EMAIL_RE.sub("[REDACTED_EMAIL]", t)
    t = PHONE_RE.sub("[REDACTED_PHONE]", t)
    t = CARD_RE.sub("[REDACTED_CARD]", t)
    return t
