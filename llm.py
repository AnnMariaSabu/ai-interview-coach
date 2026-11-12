"""
llm.py - Talk to the local AI model through Ollama.
"""
from ollama import Client

import config

client = Client(host=config.OLLAMA_URL)


def ask_ai(prompt: str, system: str = "You are a helpful assistant.", json_mode: bool = False) -> str:
    """Send a prompt to the AI and return its text answer."""
    response = client.chat(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": config.TEMPERATURE},
        format="json" if json_mode else None,
    )
    return response["message"]["content"]