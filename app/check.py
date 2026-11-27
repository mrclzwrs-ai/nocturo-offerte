"""Website-check & verkoopplan: het kantoor leest de website van de klant en maakt er
verbeterpunten en een verkoopplan voor particulieren van. Hoort bij Video Ads.
"""
import ipaddress
import json
import re
import socket
import threading
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

from .models import SessionLocal, WebsiteCheck

PER_MAAND = 4      # met Video Ads
PROEF = 1          # zonder Video Ads
MAX_BYTES = 1_500_000
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NocturoCheck/1.0; +https://nocturoapps.com)"}
TAALNAAM = {"nl": "Nederlands", "en": "English", "de": "Deutsch", "fr": "Français", "es": "Español"}


# ---------- website lezen ----------
class _Lezer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tekst, self.links, self.fotos = [], [], []
        self.titel, self.beschrijving, self._skip, self._in_titel = "", "", 0, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript", "svg"):
            self._skip += 1
        elif tag == "title":
            self._in_titel = True
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            if src and not src.startswith("data:"):
                self.fotos.append(src)
        elif tag == "meta":
            naam = (a.get("name") or a.get("property") or "").lower()
            if naam in ("description", "og:description") and not self.beschrijving:
                self.beschrijving = a.get("content") or ""
            if naam == "og:image" and a.get("content"):
                self.fotos.insert(0, a["content"])

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_titel = False

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_titel:
            self.titel += data.strip()
        t = data.strip()
        if t:
            self.tekst.append(t)


def _veilig(url: str) -> bool:
    """Geen interne adressen ophalen."""
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.hostname:
            return False
        for info in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        return True
    except Exception:
        return False


def _haal(url: str):
    if not _veilig(url):
        return None, url
    r = requests.get(url, headers=HEADERS, timeout=15, stream=True, allow_redirects=True)
    if not _veilig(r.url):
        return None, r.url
    data = r.raw.read(MAX_BYTES, decode_content=True)
    if "html" not in (r.headers.get("content-type") or "html"):
        return None, r.url
    return data.decode(r.encoding or "utf-8", errors="replace"), r.url


WOORDEN_SUB = ("product", "products", "collections", "shop", "winkel", "assortiment", "over", "about",
               "ons", "aanbod", "diensten", "services", "menu", "producten", "categorie", "category")


SOCIAAL = {"Instagram": ["instagram.com"], "Facebook": ["facebook.com", "fb.com"], "TikTok": ["tiktok.com"],
           "YouTube": ["youtube.com", "youtu.be"], "LinkedIn": ["linkedin.com"], "X": ["x.com", "twitter.com"],
           "Threads": ["threads.net", "threads.com"], "Reddit": ["reddit.com"], "Pinterest": ["pinterest.com"]}


def lees_website(start: str) -> dict:
    if not start.startswith("http"):
        start = "https://" + start.strip()
    html, eind = _haal(start)
    if not html:
        raise RuntimeError("De website kon niet worden geopend.")
    hoofd = _Lezer()
    hoofd.feed(html)
    host = urlparse(eind).hostname
    kandidaten = []
    for href in hoofd.links:
        u = urljoin(eind, href).split("#")[0]
        p = urlparse(u)
        if p.hostname != host or u in kandidaten or u.rstrip("/") == eind.rstrip("/"):
            continue
        if any(w in p.path.lower() for w in WOORDEN_SUB):
            kandidaten.append(u)
    paginas = [{"url": eind, "titel": hoofd.titel, "beschrijving": hoofd.beschrijving,
                "tekst": " ".join(hoofd.tekst)[:6000]}]
    fotos = [urljoin(eind, f) for f in hoofd.fotos]
    for u in kandidaten[:4]:
        try:
            h, ue = _haal(u)
        except Exception:
            continue
        if not h:
            continue
        lz = _Lezer()
        lz.feed(h)
        paginas.append({"url": ue, "titel": lz.titel, "beschrijving": lz.beschrijving,
                        "tekst": " ".join(lz.tekst)[:3500]})
        fotos += [urljoin(ue, f) for f in lz.fotos]
    schoon = []
    for f in fotos:
        if f.startswith("http") and f not in schoon and not re.search(r"(logo|icon|sprite|pixel|badge|payment)", f, re.I):
            schoon.append(f)
    socials = {}
    for href in hoofd.links:
        u = urljoin(eind, href)
        h = (urlparse(u).hostname or "").lower().replace("www.", "").replace("m.", "", 1)
        for naam, dom in SOCIAAL.items():
            if any(h == d or h.endswith("." + d) for d in dom) and naam not in socials:
                socials[naam] = u
    return {"start": eind, "paginas": paginas, "fotos": schoon[:12], "socials": socials}


# ---------- Claude ----------
TOOL = {
    "name": "website_rapport",
    "description": "Geef het rapport over de website en het verkoopplan terug.",
    "input_schema": {
        "type": "object",
        "properties": {
            "winkelnaam": {"type": "string", "description": "naam van de winkel zoals op de website"},
            "samenvatting": {"type": "string", "description": "2-3 zinnen: wat verkoopt deze zaak en voor wie"},
            "sterke_punten": {"type": "array", "items": {"type": "string"}, "description": "2-4 dingen die al goed zijn"},
            "verbeterpunten": {
                "type": "array",
                "items": {"type": "object", "properties": {
                    "titel": {"type": "string", "description": "korte titel, 3-7 woorden, nooit leeg"},
                    "uitleg": {"type": "string", "description": "wat er beter kan en hoe, 1-3 zinnen, gewone taal"},
                    "belang": {"type": "string", "enum": ["hoog", "middel", "laag"]}},
                    "required": ["titel", "uitleg", "belang"]},
                "description": "5-8 concrete verbeterpunten, belangrijkste eerst"},
            "kanalen": {
                "type": "array",
                "items": {"type": "object", "properties": {
                    "kanaal": {"type": "string"}, "waarom": {"type": "string"}, "hoe_vaak": {"type": "string"}},
                    "required": ["kanaal", "waarom", "hoe_vaak"]},
                "description": "2-4 kanalen om particulieren te bereiken"},
            "producten_eerst": {
                "type": "array",
                "items": {"type": "object", "properties": {"naam": {"type": "string"}, "waarom": {"type": "string"}},
                          "required": ["naam", "waarom"]},
                "description": "2-5 producten of diensten die echt op de site staan, om mee te beginnen"},
            "weken": {
                "type": "array",
                "items": {"type": "object", "properties": {
                    "week": {"type": "integer"}, "thema": {"type": "string"},
                    "filmpjes": {"type": "array", "items": {"type": "object", "properties": {
                        "titel": {"type": "string", "description": "productnaam of kort onderwerp, max 8 woorden"},
                        "omschrijving": {"type": "string", "description": "2-4 zinnen met alleen feiten van de site, bruikbaar als productomschrijving voor een reclamefilmpje"}},
                        "required": ["titel", "omschrijving"]}}},
                    "required": ["week", "thema", "filmpjes"]},
                "description": "plan voor 4 weken, per week 2-3 filmpjes"},
            "verwachting": {"type": "string", "description": "eerlijk, 2-3 zinnen: hoe lang het meestal duurt voordat je gezien wordt, zonder beloftes of cijfers over omzet"},
        },
        "required": ["winkelnaam", "samenvatting", "sterke_punten", "verbeterpunten", "kanalen", "producten_eerst", "weken", "verwachting"],
    },
}


def maak_rapport(site: dict, naam: str, lang: str) -> dict:
    from .ai import _call_tool
    taal = TAALNAAM.get(lang, "Nederlands")
    system = (
        "Je bent een ervaren verkoper en webwinkel-adviseur die kleine ondernemers helpt meer te verkopen aan particulieren. "
        "Je bekijkt hun website door de ogen van een klant. Regels:\n"
        "- Schrijf alles in het " + taal + ", in gewone, vriendelijke taal zonder vakjargon. Spreek de ondernemer aan met 'je'.\n"
        "- Baseer je ALLEEN op wat in de aangeleverde tekst van de website staat. Verzin geen producten, prijzen, "
        "reviews of eigenschappen. Weet je iets niet zeker (bijv. omdat je de foto's niet kunt zien), zeg dat dan eerlijk.\n"
        "- Verbeterpunten moeten concreet en uitvoerbaar zijn, de belangrijkste eerst.\n"
        "- Beloof nooit omzet, aantallen klanten of resultaten.\n"
        "- De filmpjes zijn korte verticale reclamefilmpjes van één product of dienst, met foto's en een stem.\n"
        "- De ondernemer heeft deze website zelf ingevuld. Twijfel daar nooit aan en noem de naam van de winkel zoals die "
        "op de website staat. Begin de samenvatting direct met wat de winkel verkoopt en voor wie.\n"
        "- Geef elk verbeterpunt een korte, duidelijke titel van 3 tot 7 woorden.\n"
        "- Elke uitleg moet op zichzelf te begrijpen zijn, ook zonder de titel: noem altijd eerst concreet waar het over gaat "
        "(bijv. 'De belofte \"vandaag besteld, morgen in huis\" ...') en verwijs nooit met 'dit' of 'dat' naar iets wat er niet staat."
    )
    user = ("Website: " + site["start"] + "\n\nTekst van de website (per pagina):\n"
            + json.dumps(site["paginas"], ensure_ascii=False))
    from .methode import met_methode
    system = met_methode(system, "bekijk de website stap voor stap met deze methode: komt een bezoeker goed binnen (eerste indruk), wordt zijn behoefte wakker gemaakt, wordt het nut duidelijk in voordelen, worden de bekende bezwaren weggenomen (prijs, vertrouwen, gedoe), is er een duidelijke volgende stap of keuze, en is er nazorg. Baseer je verbeterpunten daarop, in gewone taal, zonder de stapnummers te noemen. De filmpjes in het plan openen met een herkenbare situatie of vraag.")
    return _call_tool(system, user, TOOL, max_tokens=6000)


def _start(check_id: int, naam: str, lang: str):
    with SessionLocal() as db:
        c = db.get(WebsiteCheck, check_id)
        if not c or c.status != "pending":
            return
        try:
            c.status = "processing"
            db.commit()
            site = lees_website(c.url)
            rapport = maak_rapport(site, naam, lang)
            rapport["fotos"] = site["fotos"]
            c.url = site["start"]
            c.result_json = json.dumps(rapport, ensure_ascii=False)
            c.status = "done"
            db.commit()
        except Exception as ex:
            print(f"Website-check {check_id} mislukt:", ex)
            c.status, c.error = "failed", str(ex)[:500]
            db.commit()


def herstel_na_herstart():
    """Bij het opstarten: checks die nog liepen toen de server stopte, opnieuw starten."""
    from .models import Company
    with SessionLocal() as db:
        lopend = db.query(WebsiteCheck).filter(WebsiteCheck.status.in_(["pending", "processing"])).all()
        for x in lopend:
            x.status = "pending"
            db.commit()
            comp = db.get(Company, x.company_id)
            start_op_achtergrond(x.id, comp.name if comp else "", (comp.lang if comp else "nl") or "nl")


def start_op_achtergrond(check_id: int, naam: str, lang: str):
    threading.Thread(target=_start, args=(check_id, naam, lang), daemon=True).start()
