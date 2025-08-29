"""Utility functions for interacting with OpenRouter API."""

from __future__ import annotations

import os
from typing import List

import httpx

from .models import ModelInfo

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


async def fetch_models() -> List[ModelInfo]:
    """Fetch model list from OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "HTTP-Referer": "https://your-app.example",
        "X-Title": "Faceless ATM MVP",
    }
    url = f"{OPENROUTER_BASE}/models"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
    data = resp.json().get("data", [])
    models: List[ModelInfo] = []
    for item in data:
        models.append(
            ModelInfo(
                id=item.get("id"),
                name=item.get("name"),
                pricing_input=float(item.get("pricing", {}).get("prompt", 0)),
                pricing_output=float(item.get("pricing", {}).get("completion", 0)),
                context_length=int(item.get("context_length", 0)),
                latency_ms=item.get("top_provider", {}).get("latency"),
                available=bool(item.get("top_provider", {}).get("is_available", True)),
                popularity=item.get("popularity"),
            )
        )
    return models


async def chat_completion(model: str, messages: List[dict], max_tokens: int = 2000) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "HTTP-Referer": "https://your-app.example",
        "X-Title": "Faceless ATM MVP",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{OPENROUTER_BASE}/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()
