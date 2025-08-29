"""Fallback to Gemini API."""

from __future__ import annotations

import os
import httpx


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


async def generate(model: str, system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    url = GEMINI_URL.format(model=model) + f"?key={api_key}" if api_key else GEMINI_URL.format(model=model)
    payload = {
        "contents": [
            {"parts": [{"text": system_prompt}]},
            {"parts": [{"text": user_prompt}]},
        ]
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
