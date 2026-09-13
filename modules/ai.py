import requests


class AIEngine:
    def __init__(self, backend="ollama", model="qwen2.5:0.5b"):
        self.backend = backend
        self.model = model

    def ask(self, prompt: str) -> str:
        if self.backend != "ollama":
            return "No AI backend is configured."
        try:
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=90,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "I could not generate a response.").strip()
        except Exception:
            return (
                "The local AI engine is not available. ORBIT core functions still work. "
                "Install and start Ollama, then download the configured small model."
            )
