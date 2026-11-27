"""Echte video (proef): een productfoto laten bewegen met Kling via fal.ai.

Nodig op de server: FAL_KEY. Dit bestand doet alleen het praten met fal.ai;
de testpagina staat in main.py onder /beheer/kling (alleen Marcel).
"""
import os
import time

import requests

QUEUE = "https://queue.fal.run"

# Modellen die we vergelijken (prijzen van fal.ai, 27 nov 2026)
MODELLEN = {
    "pro": {"id": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video", "naam": "Kling 2.5 Turbo Pro", "prijs": "$0,35 per shot"},
    "standaard": {"id": "fal-ai/kling-video/v2.1/standard/image-to-video", "naam": "Kling 2.1 Standard", "prijs": "$0,25 per shot"},
}

PROMPT = ("Cinematic product commercial shot. Slow, smooth camera push-in with a gentle orbit around the product. "
          "Soft studio lighting with subtle light sweeps and reflections. The product itself stays exactly the same "
          "shape, colour and label. Elegant, premium, calm movement.")
NEGATIEF = "blur, distortion, deformed product, changing logo, extra objects, text, watermark, people, hands"


def klaar() -> bool:
    return bool(os.environ.get("FAL_KEY", "").strip())


def _kop():
    return {"Authorization": f"Key {os.environ['FAL_KEY'].strip()}", "Content-Type": "application/json"}


def start(model_key: str, image_url: str, prompt: str = "") -> dict:
    """Zet een opdracht in de wachtrij van fal.ai. Geeft de status- en antwoordlinks terug."""
    m = MODELLEN[model_key]
    r = requests.post(f"{QUEUE}/{m['id']}", headers=_kop(), timeout=60, json={
        "prompt": prompt or PROMPT, "image_url": image_url, "duration": "5", "negative_prompt": NEGATIEF})
    if r.status_code >= 300:
        raise RuntimeError(f"fal.ai {r.status_code}: {r.text[:300]}")
    d = r.json()
    return {"request_id": d.get("request_id", ""), "status_url": d.get("status_url", ""),
            "response_url": d.get("response_url", ""), "gestart": time.time()}


def stand(job: dict) -> dict:
    """Vraagt bij fal.ai hoe het ervoor staat. Vult job['status'], en bij klaar job['url']."""
    if job.get("status") in ("klaar", "mislukt") or not job.get("status_url"):
        return job
    try:
        r = requests.get(job["status_url"], headers=_kop(), timeout=20)
        s = (r.json() or {}).get("status", "")
    except Exception as ex:  # even geen antwoord: volgende keer opnieuw
        print("fal.ai status:", ex)
        return job
    if s == "COMPLETED":
        try:
            d = requests.get(job["response_url"], headers=_kop(), timeout=30).json()
            url = ((d or {}).get("video") or {}).get("url", "")
        except Exception as ex:
            d, url = {}, ""
            print("fal.ai antwoord:", ex)
        if url:
            job["status"], job["url"] = "klaar", url
        else:
            job["status"], job["fout"] = "mislukt", str(d)[:300]
        job["duur"] = int(time.time() - job.get("gestart", time.time()))
    elif s in ("IN_QUEUE", "IN_PROGRESS"):
        job["status"] = "bezig"
    elif s:
        job["status"], job["fout"] = "mislukt", s
    return job
