import re
"""Nocturo Video Ads: dezelfde reclamefilmpjes als ShopReels, voor winkels zonder Shopify.

De klant vult een product in (naam, prijs, omschrijving, 1 tot 4 foto's). Claude schrijft
de voice-overtekst, Creatomate maakt het filmpje met het ShopReels-template v2.
Limiet: 15 filmpjes per kalendermaand met een abonnement, 3 proeffilmpjes zonder.
Nodig op de server: CREATOMATE_API_KEY (en ANTHROPIC_API_KEY, die Offerte al heeft).
"""
import json
import os
import random
import threading
import time
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
ECHT_KOST = 3          # een Echte video kost 3 filmpjes van het tegoed (afgesproken 27 nov 2026)
ECHT_MAX_WACHT = 20 * 60   # na 20 minuten zonder bewegend beeld geven we het op
_ACTIEF: set = set()       # Echte video's waar een achtergrondtaak zelf naar kijkt

VOICE_IDS = {
    "nl": "tfweP7lGJyLeNV9dH1Rm", "en": "laTmoAT4stwoPzthxjZT", "de": "sa2Ndyhs1V7h8EXKT9mV",
    "fr": "LFo5X4P9PhYaOLBA9Hyh", "es": "FA1FBP9TKxnBiw45fHmS",
}
# Extra stemmen (27 nov 2026): standaard ElevenLabs-stemmen die alle talen spreken.
# Leeg = de moedertaalstem per taal hierboven.
STEMMEN = {"man": "pNInz6obpgDQGcFmaJgB", "vrouw": "21m00Tcm4TlvDq8ikWAM"}
CTA = {"nl": "Bestel nu bij ", "en": "Shop now at ", "de": "Jetzt bestellen bei ",
       "fr": "Commandez sur ", "es": "Pide ahora en "}
SLOGANS = ["Op is op!", "Wacht niet te lang!", "Mis het niet!", "Snel zijn is de boodschap!"]
# Voor diensten (reading, behandeling, cursus, reparatie...): niets dat 'op' kan raken
DIENST_SLOGANS = ["Boek vandaag nog!", "Wacht niet te lang!", "Maak nu je afspraak!"]
CTA_DIENST = {"nl": "Boek nu bij ", "en": "Book now at ", "de": "Jetzt buchen bei ",
              "fr": "Réservez chez ", "es": "Reserva ya en "}
NOODTEKST = {
    "nl": "{title}. En dat voor een scherpe prijs. Bestel nu bij ons. Mis het niet!",
    "en": "{title}. And all for a great price. Order now from us. Don't miss out!",
    "de": "{title}. Und das zu einem starken Preis. Jetzt bei uns bestellen. Nicht verpassen!",
    "fr": "{title}. Et le tout à un prix imbattable. Commandez chez nous. Ne le manquez pas !",
    "es": "{title}. Y todo a un precio genial. Pídelo ya con nosotros. ¡No te lo pierdas!",
}
# Eigen achtergrondmuziek (gemaakt met Suno Pro), staat in app/static/muziek/.
# sfeer = sleutel voor de tekst in kantoor.py, stijlen = bij welke stijl het kantoor hem zelf mag kiezen.
MUZIEK = [
    {"key": "ascent-in-gold", "titel": "Ascent in Gold", "sfeer": "stoer_duur", "stijlen": ["luxe", "foto"]},
    {"key": "cool-and-confident-1", "titel": "Cool and Confident", "sfeer": "stoer_energiek", "stijlen": ["foto"]},
    {"key": "cool-and-confident-2", "titel": "Cool and Confident II", "sfeer": "stoer_energiek", "stijlen": ["foto"]},
    {"key": "fresh-start-1", "titel": "Fresh Start", "sfeer": "fris_vrolijk", "stijlen": ["licht"]},
    {"key": "fresh-start-2", "titel": "Fresh Start II", "sfeer": "fris_vrolijk", "stijlen": ["licht", "foto"]},
    {"key": "cozy-afternoon-1", "titel": "Cozy Afternoon", "sfeer": "rustig_warm", "stijlen": ["licht", "luxe"]},
    {"key": "cozy-afternoon-2", "titel": "Cozy Afternoon II", "sfeer": "rustig_warm", "stijlen": ["licht", "luxe"]},
    {"key": "inner-peace-1", "titel": "Inner Peace", "sfeer": "spiritueel", "stijlen": []},
    {"key": "inner-peace-2", "titel": "Inner Peace II", "sfeer": "spiritueel", "stijlen": []},
    {"key": "bansuri-meditation-1", "titel": "Bansuri Meditation", "sfeer": "spiritueel", "stijlen": []},
    {"key": "bansuri-meditation-2", "titel": "Bansuri Meditation II", "sfeer": "spiritueel", "stijlen": []},
]
MUZIEK_KEYS = {m["key"] for m in MUZIEK}


def kies_muziek(gekozen: str, stijl: str) -> str:
    """Sleutel van het muziekje: de keuze van de klant, anders een passend muziekje bij de stijl."""
    if gekozen in MUZIEK_KEYS:
        return gekozen
    passend = [m["key"] for m in MUZIEK if stijl in m["stijlen"]] or [m["key"] for m in MUZIEK]
    return random.choice(passend)


def klaar() -> bool:
    return bool(os.environ.get("CREATOMATE_API_KEY"))


def _telling(q) -> int:
    """Een gewoon filmpje telt 1, een Echte video telt ECHT_KOST."""
    return sum(ECHT_KOST if getattr(v, "echt", False) else 1 for v in q.all())


def gebruikt_deze_maand(db, company_id) -> int:
    nu = datetime.utcnow()
    begin = datetime(nu.year, nu.month, 1)
    return _telling(db.query(Video).filter(Video.company_id == company_id, Video.created_at >= begin,
                                           Video.status != "failed"))


def gebruikt_totaal(db, company_id) -> int:
    return _telling(db.query(Video).filter(Video.company_id == company_id, Video.status != "failed"))


def extra_deze_maand(db, company_id) -> int:
    from .models import VideoExtra
    maand = datetime.utcnow().strftime("%Y-%m")
    return sum(x.aantal or 0 for x in db.query(VideoExtra).filter(VideoExtra.company_id == company_id,
                                                                   VideoExtra.maand == maand).all())


def tegoed(db, company_id, actief: bool, plus: bool = False) -> tuple[int, int]:
    """(nog over, limiet). Plus = 40 per maand; bijgekochte pakketten tellen deze maand mee."""
    if actief:
        limiet = (40 if plus else PER_MAAND) + extra_deze_maand(db, company_id)
        return max(0, limiet - gebruikt_deze_maand(db, company_id)), limiet
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


def schrijf_voiceover(title, description, lang) -> tuple[str, bool]:
    """Geeft (tekst, is_dienst)."""
    from .ai import _client, MODEL
    slogan = random.choice(SLOGANS)
    dienst_slogan = random.choice(DIENST_SLOGANS)
    sec, woorden = lengte_voor(description)
    prompt = f"""Schrijf een enthousiaste voice-overtekst voor een verkoopvideo van maximaal {sec} seconden (maximaal {woorden} woorden) over dit product. Gebruik de ruimte alleen als de omschrijving genoeg echte informatie geeft; is er weinig informatie, houd de tekst dan kort.
Taal van de tekst: {lang} (nl = Nederlands, en = Engels, de = Duits, fr = Frans, es = Spaans).
Product: {title}
Omschrijving: {description}
Slotkreet bij een product: {slogan}
Slotkreet bij een dienst: {dienst_slogan}

Bepaal eerst of het een PRODUCT is (iets dat je koopt en meeneemt, kan uitverkocht raken) of een DIENST (iets dat iemand voor je doet of een afspraak: reading, behandeling, les, cursus, reparatie, advies, knipbeurt).
Zet op de allereerste regel alleen het woord PRODUCT of DIENST. Daaronder de voice-overtekst.

Regels:
1. Noem GEEN prijs en GEEN getallen of bedragen. De prijs staat al in beeld. Zeg in plaats daarvan iets als 'en dat voor een scherpe prijs' in de taal van de tekst.
2. Gebruik alleen eigenschappen die in de productnaam of omschrijving staan. Verzin geen eigenschappen, beloftes over levering, garantie of kortingen.
3. Geen emoji's, geen hashtags, geen aanhalingstekens en geen gedachtestreepjes.
4. Eindig met een korte oproep om te bestellen (product) of te boeken (dienst), alsof de winkel zelf praat. Noem NOOIT de naam van de winkel of het webadres, maar zeg 'bij ons' in de taal van de tekst. Zeg nooit 'link in bio'.
5. Sluit af met de slotkreet die bij het soort hoort; zeg bij een dienst nooit iets als 'op is op' of 'zolang de voorraad strekt'; is de tekst niet Nederlands, vertaal de kreet dan naar een natuurlijke kreet in die taal.
Geef alleen de tekst terug."""
    from .methode import met_methode
    systeem = met_methode("Je schrijft korte voice-overteksten voor reclamefilmpjes. De regels in de opdracht gaan altijd voor.",
                          "open met een herkenbare situatie of vraag die de kijker raakt (de eerste seconden zijn de voordeur), vertaal eigenschappen naar wat ze de kijker opleveren, en eindig met één duidelijke oproep.")
    client = _client()
    for poging in (1, 2):
        msg = client.messages.create(model=MODEL, max_tokens=2000, system=systeem,
                                     messages=[{"role": "user", "content": prompt}])
        tekst = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        if tekst:
            eerste, _, rest = tekst.partition("\n")
            soort = eerste.strip().strip(".:").upper()
            if soort in ("PRODUCT", "DIENST") and rest.strip():
                return rest.strip(), soort == "DIENST"
            return tekst, False
        soorten = [getattr(b, "type", "?") for b in msg.content]
        print(f"Voice-over leeg (poging {poging}): stop_reason={getattr(msg, 'stop_reason', '?')}, "
              f"blokken={soorten}, model={MODEL}")
    # Noodtekst, zodat de klant altijd een filmpje krijgt (alleen de productnaam, niets verzonnen).
    print("Voice-over: noodtekst gebruikt")
    return NOODTEKST.get(lang, NOODTEKST["nl"]).format(title=title), False


def _modificaties(v, bronnen: list, base_url: str, shop_name: str, website: str, lang: str, dienst: bool) -> dict:
    b1 = bronnen[0]
    b2 = bronnen[1] if len(bronnen) > 1 else b1
    b3 = bronnen[2] if len(bronnen) > 2 else b2
    b4 = bronnen[3] if len(bronnen) > 3 else b3
    return {
        "title.text": v.title, "price.text": prijs_tekst(v.price), "price.visible": bool(v.price),
        "product_image.source": b1, "image_2.source": b2, "image_3.source": b3, "image_4.source": b4,
        "voiceover_audio.source": v.voiceover,
        "voiceover_audio.provider": f"elevenlabs model_id=eleven_turbo_v2_5 voice_id={STEMMEN.get(getattr(v, 'stem', '') or '', VOICE_IDS[lang])} language_code={lang}",
        "website.text": re.sub(r"^https?://(www\.)?", "", (website or shop_name)).rstrip("/"), "cta.text": f"{(CTA_DIENST if dienst else CTA)[lang]}{shop_name}",
        "music.source": f"{base_url}/static/muziek/{kies_muziek(getattr(v, 'muziek', '') or '', getattr(v, 'stijl', '') or STANDAARD_STIJL)}.mp3"}


def _kop():
    return {"Authorization": f"Bearer {os.environ['CREATOMATE_API_KEY']}", "Content-Type": "application/json"}


def _video_bron(template_id: str) -> dict:
    """Haalt het sjabloon op en maakt van de vier foto-vakken video-vakken (voor Echte video)."""
    r = requests.get(f"https://api.creatomate.com/v1/templates/{template_id}", headers=_kop(), timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"Creatomate sjabloon {r.status_code}: {r.text[:200]}")
    bron = r.json().get("source") or {}

    def omzetten(els):
        for e in els or []:
            if e.get("type") == "composition":
                omzetten(e.get("elements"))
            elif e.get("type") == "image" and e.get("name") in ("product_image", "image_2", "image_3", "image_4"):
                e["type"], e["loop"], e["volume"] = "video", True, "0%"
                # het beeld beweegt zelf al; het langzame inzoomen van de foto's laten we weg
                e["animations"] = [a for a in e.get("animations", []) if a.get("type") != "scale"]
    omzetten(bron.get("elements"))
    bron["output_format"] = "mp4"
    return bron


def _render(v, bronnen: list, base_url: str, shop_name: str, website: str, dienst: bool):
    """Stuurt het filmpje naar Creatomate en bewaart het render-id."""
    lang = v.lang if v.lang in VOICE_IDS else "nl"
    template_id = STIJLEN.get(getattr(v, "stijl", None) or STANDAARD_STIJL, STIJLEN[STANDAARD_STIJL])
    mods = _modificaties(v, bronnen, base_url, shop_name, website, lang, dienst)
    body = {"modifications": mods}
    if getattr(v, "echt", False):
        body["source"] = _video_bron(template_id)
    else:
        body["template_id"] = template_id
    r = requests.post("https://api.creatomate.com/v1/renders", timeout=60, headers=_kop(), json=body)
    if r.status_code >= 300:
        raise RuntimeError(f"Creatomate {r.status_code}: {r.text[:200]}")
    data = r.json()
    render = data[0] if isinstance(data, list) else data
    v.render_id = render.get("id", "")


def _start(video_id: int, base_url: str, shop_name: str, website: str):
    echt = False
    with SessionLocal() as db:
        v = db.get(Video, video_id)
        if not v or v.status != "pending":
            return
        try:
            v.status = "processing"
            db.commit()
            lang = v.lang if v.lang in VOICE_IDS else "nl"
            v.voiceover, dienst = schrijf_voiceover(v.title, v.description, lang)
            if not v.voiceover:
                raise RuntimeError("Geen voice-overtekst")
            fotos = [f"{base_url}/media/{t}" for t in v.media_tokens.split(",") if t]
            echt = bool(getattr(v, "echt", False))
            if echt:
                from . import kling as KL
                if not KL.klaar():
                    raise RuntimeError("FAL_KEY ontbreekt")
                jobs = [KL.start(KL.ECHT_MODEL, f, KL.PROMPT_ECHT) for f in fotos]
                v.kling = json.dumps({"jobs": jobs, "base_url": base_url, "shop": shop_name, "site": website,
                                      "dienst": dienst, "gestart": time.time()})
                db.commit()
            else:
                _render(v, fotos, base_url, shop_name, website, dienst)
                db.commit()
        except Exception as ex:
            print(f"Video {video_id} mislukt:", ex)
            v.status = "failed"
            v.error = str(ex)[:500]
            db.commit()
            return
    if echt:
        # Zelf blijven kijken tot de bewegende shots klaar zijn, ook als de klant de pagina dichtdoet.
        _ACTIEF.add(video_id)
        try:
            while True:
                time.sleep(10)
                with SessionLocal() as db:
                    v = db.get(Video, video_id)
                    if not v or v.status != "processing" or v.render_id:
                        return
                    kling_verder(db, v)
                    if v.status != "processing" or v.render_id:
                        return
        finally:
            _ACTIEF.discard(video_id)


def kling_verder(db, v):
    """Echte video: vraagt fal.ai hoe het met de shots staat; zijn ze allemaal klaar, dan naar Creatomate."""
    from . import kling as KL
    try:
        info = json.loads(v.kling or "{}")
    except ValueError:
        info = {}
    jobs = info.get("jobs") or []
    if not jobs:
        return
    for job in jobs:
        KL.stand(job)
    v.kling = json.dumps(info)
    if any(j.get("status") == "mislukt" for j in jobs):
        v.status, v.error = "failed", "Bewegend beeld mislukt: " + "; ".join(j.get("fout", "") for j in jobs if j.get("fout"))[:400]
    elif all(j.get("status") == "klaar" for j in jobs):
        try:
            _render(v, [j["url"] for j in jobs], info.get("base_url", ""), info.get("shop", ""), info.get("site", ""),
                    bool(info.get("dienst")))
            print(f"Video {v.id}: bewegend beeld klaar na {int(time.time() - info.get('gestart', time.time()))} sec")
        except Exception as ex:
            v.status, v.error = "failed", str(ex)[:500]
    elif time.time() - info.get("gestart", time.time()) > ECHT_MAX_WACHT:
        v.status, v.error = "failed", "Bewegend beeld duurde te lang"
    db.commit()


def start_op_achtergrond(video_id, base_url, shop_name, website):
    threading.Thread(target=_start, args=(video_id, base_url, shop_name, website), daemon=True).start()


def ververs(db, videos):
    """Vraagt bij Creatomate de stand op van filmpjes die nog bezig zijn."""
    if not klaar():
        return
    for v in videos:
        if v.status == "processing" and getattr(v, "echt", False) and not v.render_id:
            if v.id not in _ACTIEF and v.kling:
                kling_verder(db, v)   # reserve: als de achtergrondtaak door een herstart is gestopt
            continue
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
