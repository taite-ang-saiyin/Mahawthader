import asyncio
import requests
import json

class LLMHandler:
    """
    LLM handler using Ollama local server (gemma3:4b).
    No API key required; runs locally.
    """

    def __init__(self, host: str = "http://127.0.0.1:11434"):
        self.host = host
        self.model_name = "gemma3:4b"   # ✅ updated model name

    async def generate_text(self, model_name: str, prompt: str, max_tokens: int = 500) -> str:
        """
        Async wrapper to generate text from Ollama model.
        """
        return await self._call_ollama(prompt, max_tokens)

    async def analyze_text(self, scenario: str, law_text: str) -> str:
        """
        Send scenario + law text to LLM and get structured legal analysis.
        """
        prompt = f"""
        Given the following scenario:

        {scenario}

        And the following relevant laws:

        {law_text}

        Provide a structured legal analysis discussing:
        - Which legal elements are satisfied
        - Which defenses may apply
        - The likely outcome
        """

        
        return await self._call_ollama(prompt, max_tokens=1000)

    async def raw_call(self, prompt: str) -> str:
        """
        Direct LLM call for any text processing task.
        """
        return await self._call_ollama(prompt, max_tokens=500)

    async def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Internal helper: POST request to Ollama local server (/api/generate).
        """
        url = f"{self.host}/api/generate"   # ✅ correct endpoint
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,         # ✅ disables chunked streaming
            "num_predict": max_tokens
        }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, headers=headers))

        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error {response.status_code}: {response.text}")

        data = response.json()
        if "response" in data:   # ✅ Ollama returns "response"
            return data["response"].strip()
        return str(data)
