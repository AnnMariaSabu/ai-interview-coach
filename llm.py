"""
llm.py - Talk to the local AI model through Ollama.
"""
import time

from ollama import Client

import config

client = Client(host=config.OLLAMA_URL)

KEEP_MODEL_LOADED = "30m"  # keep the model in memory, so it does not reload between calls


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

    start = time.perf_counter()  # ⏱️ start the stopwatch
    response = client.chat(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": config.TEMPERATURE},
        format=output_format,
        keep_alive=KEEP_MODEL_LOADED,
    )
    seconds = time.perf_counter() - start  # ⏱️ stop the stopwatch
    form_name = json_schema.get("title", "text") if json_schema else "text"
    print(f"[timer] AI call for '{form_name}' took {seconds:.1f} seconds")

    return response["message"]["content"]


def embed(texts: list[str]) -> list[list[float]]:
    """Turn each text into a list of numbers that captures its meaning."""
    start = time.perf_counter()
    response = client.embed(model=config.EMBED_MODEL, input=texts, keep_alive=KEEP_MODEL_LOADED)
    print(f"[timer] Embeddings for {len(texts)} texts took {time.perf_counter() - start:.1f} seconds")
    return response["embeddings"]