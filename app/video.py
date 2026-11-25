"""Nocturo Video Ads: dezelfde reclamefilmpjes als ShopReels, voor winkels zonder Shopify.

De klant vult een product in (naam, prijs, omschrijving, 1 tot 4 foto's). Claude schrijft
de voice-overtekst, Creatomate maakt het filmpje met het ShopReels-template v2.
Limiet: 15 filmpjes per kalendermaand met een abonnement, 3 proeffilmpjes zonder.
Nodig op de server: CREATOMATE_API_KEY (en ANTHROPIC_API_KEY, die Offerte al heeft).
"""
import os
import random
import threading
from datetime import datetime

import requests

from .models import SessionLocal, Video

TEMPLATE_ID = os.environ.get("CREATOMATE_TEMPLATE_ID", "57d4692e-4428-4563-b410-93ab5a62b120")  # oude stijl
STIJLEN = {
    "foto": "210eac12-694a-4c54-a5f2-043a98dec42b",   # Foto vol
    "luxe": "0786ffbc-0b61-4330-86e2-f0c0c4b8a6f0",   # Luxe
    "licht": "9a180322-b407-4c63-bfb9-2281e98b5018",  # Strak licht
}
STANDAARD_STIJL = "foto"
PER_MAAND = 15
PROEF = 3

VOICE_IDS = {
    "nl": "tfweP7lGJyLeNV9dH1Rm", "en": "laTmoAT4stwoPzthxjZT", "de": "sa2Ndyhs1V7h8EXKT9mV",
    "fr": "LFo5X4P9PhYaOLBA9Hyh", "es": "FA1FBP9TKxnBiw45fHmS",
}
CTA = {"nl": "Bestel nu bij ", "en": "Shop now at ", "de": "Jetzt bestellen bei ",
       "fr": "Commandez sur ", "es": "Pide ahora en "}
SLOGANS = ["Op is op!", "Wacht niet te lang!", "Mis het niet!", "Snel zijn is de boodschap!"]
NOODTEKST = {
    "nl": "{title}. En dat voor een scherpe prijs. Bestel nu bij ons. Mis het niet!",
    "en": "{title}. And all for a great price. Order now from us. Don't miss out!",
    "de": "{title}. Und das zu einem starken Preis. Jetzt bei uns bestellen. Nicht verpassen!",
    "fr": "{title}. Et le tout à un prix imbattable. Commandez chez nous. Ne le manquez pas !",
    "es": "{title}. Y todo a un precio genial. Pídelo ya con nosotros. ¡No te lo pierdas!",
}
MUSIC = ["https://cdn.creatomate.com/demo/music1.mp3", "https://cdn.creatomate.com/demo/music2.mp3",
         "https://cdn.creatomate.com/demo/music3.mp3"]


def klaar() -> bool:
    return bool(os.environ.get("CREATOMATE_API_KEY"))


def gebruikt_deze_maand(db, company_id) -> int:
    nu = datetime.utcnow()
    begin = datetime(nu.year, nu.month, 1)
    return db.query(Video).filter(Video.company_id == company_id, Video.created_at >= begin,
                                  Video.status != "failed").count()


def gebruikt_totaal(db, company_id) -> int:
    return db.query(Video).filter(Video.company_id == company_id, Video.status != "failed").count()


def tegoed(db, company_id, actief: bool) -> tuple[int, int]:
    """(nog over, limiet)"""
    if actief:
        return max(0, PER_MAAND - gebruikt_deze_maand(db, company_id)), PER_MAAND
    return max(0, PROEF - gebruikt_totaal(db, company_id)), PROEF


def prijs_tekst(p: float) -> str:
    return f"€ {(p or 0):.2f}".replace(".", ",")


def lengte_voor(description: str) -> tuple[int, int]:
    """Hoe meer de klant vertelt, hoe langer de stem mag praten: (seconden, woorden)."""
    n = len((description or "").split())
    if n < 15:
        return 14, 35
    if n < 45:
        return 22, 55
    return 30, 75


def schrijf_voiceover(title, description, lang) -> str:
    from .ai import _client, MODEL
    slogan = random.choice(SLOGANS)
    sec, woorden = lengte_voor(description)
    prompt = f"""Schrijf een enthousiaste voice-overtekst voor een verkoopvideo van maximaal {sec} seconden (maximaal {woorden} woorden) over dit product. Gebruik de ruimte alleen als de omschrijving genoeg echte informatie geeft; is er weinig informatie, houd de tekst dan kort.
Taal van de tekst: {lang} (nl = Nederlands, en = Engels, de = Duits, fr = Frans, es = Spaans).
Product: {title}
Omschrijving: {description}
Slotkreet: {slogan}

Regels:
1. Noem GEEN prijs en GEEN getallen of bedragen. De prijs staat al in beeld. Zeg in plaats daarvan iets als 'en dat voor een scherpe prijs' in de taal van de tekst.
2. Gebruik alleen eigenschappen die in de productnaam of omschrijving staan. Verzin geen eigenschappen, beloftes over levering, garantie of kortingen.
3. Geen emoji's, geen hashtags, geen aanhalingstekens en geen gedachtestreepjes.
4. Eindig met een korte oproep om te bestellen, alsof de winkel zelf praat. Noem NOOIT de naam van de winkel of het webadres, maar zeg 'bij ons' in de taal van de tekst. Zeg nooit 'link in bio'.
5. Sluit af met de slotkreet hierboven; is de tekst niet Nederlands, vertaal de kreet dan naar een natuurlijke kreet in die taal.
Geef alleen de tekst terug."""
    client = _client()
    for poging in (1, 2):
        msg = client.messages.create(model=MODEL, max_tokens=2000,
                                     messages=[{"role": "user", "content": prompt}])
        tekst = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        if tekst:
            return tekst
        soorten = [getattr(b, "type", "?") for b in msg.content]
        print(f"Voice-over leeg (poging {poging}): stop_reason={getattr(msg, 'stop_reason', '?')}, "
              f"blokken={soorten}, model={MODEL}")
    # Noodtekst, zodat de klant altijd een filmpje krijgt (alleen de productnaam, niets verzonnen).
    print("Voice-over: noodtekst gebruikt")
    return NOODTEKST.get(lang, NOODTEKST["nl"]).format(title=title)


def _start(video_id: int, base_url: str, shop_name: str, website: str):
    with SessionLocal() as db:
        v = db.get(Video, video_id)
        if not v or v.status != "pending":
            return
        try:
            v.status = "processing"
            db.commit()
            lang = v.lang if v.lang in VOICE_IDS else "nl"
            v.voiceover = schrijf_voiceover(v.title, v.description, lang)
            if not v.voiceover:
                raise RuntimeError("Geen voice-overtekst")
            fotos = [f"{base_url}/media/{t}" for t in v.media_tokens.split(",") if t]
            f1 = fotos[0]
            f2 = fotos[1] if len(fotos) > 1 else f1
            f3 = fotos[2] if len(fotos) > 2 else f2
            f4 = fotos[3] if len(fotos) > 3 else f3
            template_id = STIJLEN.get(getattr(v, "stijl", None) or STANDAARD_STIJL, STIJLEN[STANDAARD_STIJL])
            r = requests.post("https://api.creatomate.com/v1/renders", timeout=60, headers={
                "Authorization": f"Bearer {os.environ['CREATOMATE_API_KEY']}", "Content-Type": "application/json"},
                json={"template_id": template_id, "modifications": {
                    "title.text": v.title, "price.text": prijs_tekst(v.price),
                    "product_image.source": f1, "image_2.source": f2, "image_3.source": f3, "image_4.source": f4,
                    "voiceover_audio.source": v.voiceover,
                    "voiceover_audio.provider": f"elevenlabs model_id=eleven_turbo_v2_5 voice_id={VOICE_IDS[lang]} language_code={lang}",
                    "website.text": website or shop_name, "cta.text": f"{CTA[lang]}{shop_name}",
                    "music.source": random.choice(MUSIC)}})
            if r.status_code >= 300:
                raise RuntimeError(f"Creatomate {r.status_code}: {r.text[:200]}")
            data = r.json()
            render = data[0] if isinstance(data, list) else data
            v.render_id = render.get("id", "")
            db.commit()
        except Exception as ex:
            print(f"Video {video_id} mislukt:", ex)
            v.status = "failed"
            v.error = str(ex)[:500]
            db.commit()


def start_op_achtergrond(video_id, base_url, shop_name, website):
    threading.Thread(target=_start, args=(video_id, base_url, shop_name, website), daemon=True).start()


def ververs(db, videos):
    """Vraagt bij Creatomate de stand op van filmpjes die nog bezig zijn."""
    if not klaar():
        return
    for v in videos:
        if v.status != "processing" or not v.render_id:
            continue
        try:
            r = requests.get(f"https://api.creatomate.com/v1/renders/{v.render_id}", timeout=15,
                             headers={"Authorization": f"Bearer {os.environ['CREATOMATE_API_KEY']}"})
            d = r.json()
        except Exception:
            continue
        if d.get("status") == "succeeded" and d.get("url"):
            v.status, v.url, v.thumb = "completed", d["url"], d.get("snapshot_url") or ""
        elif d.get("status") == "failed":
            v.status, v.error = "failed", str(d.get("error_message") or "Render mislukt")[:500]
    db.commit()
