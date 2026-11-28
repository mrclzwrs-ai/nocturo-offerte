"""Het slimme deel: Claude leest de wens van de klant en maakt er offerteregels van."""
import json
import os
import re

from .i18n import LANG_NAMES

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")


class AIError(Exception):
    pass


QUOTE_TOOL = {
    "name": "maak_offerte",
    "description": "Geef de offerte terug als gestructureerde gegevens.",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_name": {"type": "string", "description": "Naam van de contactpersoon, leeg als onbekend"},
            "customer_company": {"type": "string", "description": "Bedrijfsnaam van de klant, leeg als onbekend"},
            "customer_email": {"type": "string", "description": "E-mailadres van de klant, leeg als onbekend"},
            "customer_address": {"type": "string", "description": "Adres van de klant, leeg als onbekend"},
            "title": {"type": "string", "description": "Kort onderwerp van de offerte (max 8 woorden)"},
            "intro": {"type": "string", "description": "Korte persoonlijke inleiding (2-3 zinnen) die laat zien dat je de wens begrijpt"},
            "closing": {"type": "string", "description": "Korte afsluiting (1-2 zinnen), uitnodigend, met eventuele levertijd/deadline uit de wens"},
            "lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": ["integer", "null"], "description": "id uit de prijslijst, of null als het er niet in staat"},
                        "description": {"type": "string"},
                        "qty": {"type": "number"},
                        "unit": {"type": "string"},
                        "price": {"type": ["number", "null"], "description": "prijs per eenheid excl. btw; null als die niet in de prijslijst staat"},
                        "vat": {"type": "number", "description": "btw-percentage"},
                    },
                    "required": ["description", "qty", "unit", "price", "vat"],
                },
            },
            "notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Korte punten die de verkoper moet nakijken (ontbrekende info, aannames, ontbrekende prijzen). In de taal van de verkoper.",
            },
        },
        "required": ["title", "intro", "closing", "lines", "notes"],
    },
}

IMPORT_TOOL = {
    "name": "prijslijst",
    "description": "Geef de producten/diensten uit de geplakte prijslijst terug.",
    "input_schema": {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "unit": {"type": "string"},
                        "price": {"type": "number", "description": "excl. btw"},
                        "vat": {"type": "number"},
                    },
                    "required": ["name", "unit", "price", "vat"],
                },
            }
        },
        "required": ["products"],
    },
}


def _client():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise AIError("ANTHROPIC_API_KEY ontbreekt")
    import anthropic

    return anthropic.Anthropic(api_key=key)


def _call_tool(system: str, user: str, tool: dict, max_tokens: int = 4000, zoeken: int = 0) -> dict:
    # Dit model ondersteunt geen geforceerde tool-keuze; daarom vragen we het
    # dringend in de instructie en proberen we het zo nodig één keer opnieuw.
    client = _client()
    system = system + f"\n\nGeef je antwoord ALTIJD via de tool '{tool['name']}', zonder losse tekst."
    tools = [tool]
    if zoeken:
        # Zoekmachine (server-tool): het model zoekt zelf op internet en antwoordt daarna via de tool.
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": zoeken}, tool]
    for _ in range(2):
        messages = [{"role": "user", "content": user}]
        for _ronde in range(4):
            try:
                c2 = client.with_options(timeout=480, max_retries=1) if zoeken else client
                msg = c2.messages.create(
                    model=MODEL,
                    max_tokens=max_tokens,
                    system=system,
                    tools=tools,
                    tool_choice={"type": "auto"},
                    messages=messages,
                )
            except Exception as e:  # netwerk, sleutel, tegoed
                print(f"[ai] {tool['name']}: fout bij aanroep:", str(e)[:300], flush=True)
                raise AIError(str(e)) from e
            if zoeken:
                soorten = [getattr(b, "type", "?") for b in msg.content]
                print(f"[ai] {tool['name']} ronde {_ronde}: stop={getattr(msg, 'stop_reason', '')} blokken={soorten}", flush=True)
            for block in msg.content:
                if getattr(block, "type", "") == "tool_use" and block.name == tool["name"]:
                    return block.input
            if getattr(msg, "stop_reason", "") == "pause_turn":
                # lange zoekbeurt: laat het model verder gaan waar het was
                messages = [{"role": "user", "content": user}, {"role": "assistant", "content": msg.content}]
                continue
            if zoeken:
                # klaar met zoeken maar nog geen antwoord: vraag om het antwoord via de tool
                messages = [{"role": "user", "content": user}, {"role": "assistant", "content": msg.content},
                            {"role": "user", "content": f"Geef nu je volledige antwoord via de tool '{tool['name']}'."}]
                continue
            break
    raise AIError("Geen antwoord van het model")


def make_quote(company, products, request_text: str, quote_lang: str) -> dict:
    if os.environ.get("FAKE_AI") == "1":
        return _fake_quote(products, request_text)

    pricelist = [
        {"id": p.id, "naam": p.name, "omschrijving": p.description, "eenheid": p.unit,
         "prijs_excl_btw": p.price, "btw": p.vat}
        for p in products
    ]
    system = (
        "Je bent de offerte-assistent van het bedrijf '" + company.name + "'. "
        "Je maakt van de wens van een klant een duidelijke, overtuigende offerte. Regels:\n"
        "- Gebruik ALLEEN prijzen uit de prijslijst. Verzin nooit een prijs. Staat iets er niet in, zet price op null "
        "en noem het in notes.\n"
        "- Kies bij staffelprijzen of varianten de prijs die past bij het gevraagde aantal.\n"
        "- Voeg logische vaste kosten uit de prijslijst toe als ze er duidelijk bij horen (bv. instelkosten, zeefkosten, verzending) "
        "en meld dat in notes.\n"
        "- Neem aantallen precies over uit de wens. Is een aantal onduidelijk, kies een redelijke aanname en meld die in notes.\n"
        "- Btw: neem het btw-percentage uit de prijslijst; anders " + f"{company.default_vat:g}" + "%.\n"
        "- Schrijf title, intro, closing en de omschrijvingen van de regels in het "
        + LANG_NAMES.get(quote_lang, "Nederlands")
        + ". Schrijf de notes in het " + LANG_NAMES.get(company.lang, "Nederlands") + ".\n"
        "- Toon: vriendelijk, zakelijk, zelfverzekerd. Geen overdreven verkooppraat. Spreek de klant aan zoals in de wens gebruikelijk "
        "(in het Nederlands met 'je', tenzij de klant zelf formeel schrijft).\n"
        "- Haal naam, bedrijf, e-mail en adres van de klant uit de tekst als ze erin staan."
    )
    user = (
        "PRIJSLIJST (JSON):\n" + json.dumps(pricelist, ensure_ascii=False) +
        "\n\nWENS VAN DE KLANT:\n" + request_text.strip()
    )
    from .methode import met_methode
    system = met_methode(system, "in de intro spiegel je de wens van de klant terug in één zin (stap 5), in de omschrijvingen noem je kort wat het de klant oplevert (stap 6), en in de afsluiting geef je één makkelijke volgende stap, waar passend als keuze tussen twee ja's (stap 8), plus dat de klant altijd mag bellen of mailen met vragen (stap 9). De prijsregels hierboven blijven altijd voorgaan; verzin nooit prijzen, kortingen of beloftes.")
    data = _call_tool(system, user, QUOTE_TOOL)
    return _clean_quote(data, products, company.default_vat)


def _clean_quote(data: dict, products, default_vat: float) -> dict:
    by_id = {p.id: p for p in products}
    lines = []
    for ln in data.get("lines") or []:
        pid = ln.get("product_id")
        price = ln.get("price")
        # veiligheid: als er een product gekozen is, altijd de echte prijs uit de lijst
        if pid in by_id and price is None:
            price = by_id[pid].price
        try:
            qty = float(ln.get("qty") or 1)
        except (TypeError, ValueError):
            qty = 1.0
        try:
            vat = float(ln.get("vat") if ln.get("vat") is not None else default_vat)
        except (TypeError, ValueError):
            vat = default_vat
        lines.append({
            "description": str(ln.get("description") or "").strip(),
            "qty": qty,
            "unit": str(ln.get("unit") or "").strip(),
            "price": None if price is None else round(float(price), 2),
            "vat": vat,
        })
    return {
        "customer_name": (data.get("customer_name") or "").strip(),
        "customer_company": (data.get("customer_company") or "").strip(),
        "customer_email": (data.get("customer_email") or "").strip(),
        "customer_address": (data.get("customer_address") or "").strip(),
        "title": (data.get("title") or "").strip(),
        "intro": (data.get("intro") or "").strip(),
        "closing": (data.get("closing") or "").strip(),
        "lines": lines,
        "notes": [str(n).strip() for n in (data.get("notes") or []) if str(n).strip()],
    }


def import_pricelist(text: str, company) -> list:
    if os.environ.get("FAKE_AI") == "1":
        out = []
        for row in text.splitlines():
            m = re.match(r"\s*(.+?)\s*[-:;\t]\s*€?\s*([\d.,]+)", row)
            if m:
                out.append({"name": m.group(1), "description": "", "unit": "stuk",
                            "price": float(m.group(2).replace(".", "").replace(",", ".")), "vat": company.default_vat})
        return out
    system = (
        "Je zet een geplakte prijslijst om naar losse producten/diensten. Prijzen excl. btw. "
        "Staat er 'incl. btw', reken dan terug naar excl. Neem staffels of varianten op als aparte regels "
        "met een duidelijke naam (bv. 'T-shirt bedrukken 1 kleur, 25-49 st.'). Eenheid kort (stuk, uur, m², set). "
        "Onbekende btw: " + f"{company.default_vat:g}" + "%. Houd de taal van de lijst aan."
    )
    data = _call_tool(system, text.strip(), IMPORT_TOOL, max_tokens=8000)
    out = []
    for p in data.get("products") or []:
        try:
            out.append({
                "name": str(p["name"]).strip()[:255],
                "description": str(p.get("description") or "").strip(),
                "unit": str(p.get("unit") or "").strip()[:50],
                "price": round(float(p["price"]), 2),
                "vat": float(p.get("vat") if p.get("vat") is not None else company.default_vat),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _fake_quote(products, text):
    """Alleen voor testen zonder sleutel."""
    lines = []
    for p in products[:3]:
        lines.append({"description": p.name, "qty": 10, "unit": p.unit, "price": p.price, "vat": p.vat})
    lines.append({"description": "Iets wat niet in de lijst staat", "qty": 1, "unit": "stuk", "price": None, "vat": 21})
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    return {
        "customer_name": "Sanne", "customer_company": "Bakkerij De Korrel",
        "customer_email": email.group(0) if email else "", "customer_address": "",
        "title": "T-shirts met logo", "intro": "Leuk dat je aan ons denkt! Hierbij de offerte.",
        "closing": "We kunnen vóór 15 december leveren.", "lines": lines,
        "notes": ["Testmodus: dit is een nep-offerte.", "Prijs ontbreekt voor één regel."],
    }
