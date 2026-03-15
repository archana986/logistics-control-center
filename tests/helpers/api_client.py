from __future__ import annotations

import httpx


def get_json(base_url: str, path: str) -> tuple[int, object]:
    response = httpx.get(f"{base_url}{path}", timeout=60)
    return response.status_code, response.json()


def post_json(base_url: str, path: str, payload: dict) -> tuple[int, object]:
    response = httpx.post(f"{base_url}{path}", json=payload, timeout=90)
    return response.status_code, response.json()
