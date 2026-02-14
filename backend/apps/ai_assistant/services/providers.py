import os
import json
import urllib.request
from dataclasses import dataclass

@dataclass
class AIResult:
    text: str
    confidence: float = 0.0
    sources: list[str] = None

class BaseProvider:
    def generate(self, system: str, prompt: str, max_tokens: int = 600) -> AIResult:
        raise NotImplementedError

class DummyProvider(BaseProvider):
    """
    Safe offline fallback: returns a templated response (still useful for MVP).
    """
    def generate(self, system: str, prompt: str, max_tokens: int = 600) -> AIResult:
        return AIResult(
            text="REPLY:\nThank you for reaching out. We’ve noted your request and will assist you shortly. "
                 "If this involves policy exceptions (refund/discount/override), we’ll confirm with our manager.\n"
                 "CONFIDENCE: 0.35\nSOURCES: \n",
            confidence=0.35,
            sources=[],
        )

class CustomHTTPProvider(BaseProvider):
    """
    Call your own AI gateway (recommended for multi-tenant control).
    Expects JSON: {system, prompt, max_tokens} -> {text}
    """
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def generate(self, system: str, prompt: str, max_tokens: int = 600) -> AIResult:
        payload = json.dumps({"system": system, "prompt": prompt, "max_tokens": max_tokens}).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data.get("text", "")
        return AIResult(text=text, confidence=float(data.get("confidence", 0.0)), sources=data.get("sources", []))

class OpenAIProvider(BaseProvider):
    """
    Minimal stub. Keep it optional to avoid hard dependency.
    Implement using your preferred OpenAI client in your project.
    """
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def generate(self, system: str, prompt: str, max_tokens: int = 600) -> AIResult:
        # Implement in your project using openai python SDK.
        # Return AIResult(text=..., confidence=..., sources=...)
        raise NotImplementedError("OpenAIProvider not wired. Use CustomHTTPProvider or implement SDK call.")

def get_provider(provider_name: str, model: str = "") -> BaseProvider:
    provider_name = (provider_name or "dummy").lower()
    if provider_name == "custom_http":
        endpoint = os.environ.get("AI_CUSTOM_HTTP_ENDPOINT", "")
        return CustomHTTPProvider(endpoint=endpoint)
    if provider_name == "openai":
        return OpenAIProvider(
            api_key=os.environ.get("AI_OPENAI_API_KEY", ""),
            model=model or os.environ.get("AI_MODEL", "gpt-4.1-mini"),
        )
    return DummyProvider()
