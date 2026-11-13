"""
llm.py - Talk to the local AI model through Ollama.
"""
from ollama import Client

import config

client = Client(host=config.OLLAMA_URL)


def ask_ai(
    prompt: str,
    system: str = "You are a helpful assistant.",
    json_mode: bool = False,
    json_schema: dict | None = None,
) -> str:
    """Send a prompt to the AI and return its text answer."""
    if json_schema is not None:
        output_format = json_schema   # strict: the answer must fit this exact form
    elif json_mode:
        output_format = "json"        # any JSON
    else:
        output_format = None          # normal text

    response = client.chat(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": config.TEMPERATURE},
        format=output_format,
    )
    return response["message"]["content"]


def embed(texts: list[str]) -> list[list[float]]:
    """Turn each text into a list of numbers that captures its meaning."""
    response = client.embed(model=config.EMBED_MODEL, input=texts)
    return response["embeddings"]