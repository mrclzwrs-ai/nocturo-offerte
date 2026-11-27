"""Voor wie werk je? Het hele kantoor gaat aan het werk voor een klant: website bekijken, doel, voorstel, filmpjes."""
import json
import threading

from .check import lees_website, TAALNAAM
from .models import Klant, SessionLocal

DOELEN = ["publiek", "klanten", "verkoop", "bekend", "anders"]

TOOL = {
    "name": "voorstel",
    "description": "Onderzoek van de website en een voorstel (funnel) om het doel van de klant te halen.",
    "input_schema": {
        "type": "object",
        "properties": {
            "wat_ze_doen": {"type": "string", "description": "Wat dit bedrijf verkoopt/doet en voor wie, 2-3 zinnen."},
            "ontdekt": {"type": "array", "items": {"type": "string"}, "description": "3-5 opvallende dingen die het team op de website ontdekte (goed én beter)."},
            "plan": {"type": "array", "description": "3-5 stappen van de funnel, in volgorde: eerst gezien worden, dan interesse, dan klant worden.",
                     "items": {"type": "object", "properties": {
                         "stap": {"type": "string", "description": "Korte titel van de stap (3-7 woorden)."},
                         "uitleg": {"type": "string", "description": "Wat we doen en waarom, 1-2 zinnen, op zichzelf te begrijpen."},
                         "robot": {"type": "string", "enum": ["speurder", "analist", "regisseur", "boekhouder"],
                                   "description": "Welke collega dit doet: speurder=nieuwe klanten zoeken en mailen, analist=website/onderzoek, regisseur=filmpjes, boekhouder=offertes."}},
                         "required": ["stap", "uitleg", "robot"]}},
            "filmpjes": {"type": "array", "description": "3 ideeën voor korte reclamefilmpjes die bij het plan horen.",
                         "items": {"type": "object", "properties": {
                             "titel": {"type": "string", "description": "Wat er in beeld komt (product of dienst), kort."},
                             "omschrijving": {"type": "string", "description": "2-3 zinnen voor de voice-over: haakje, voordeel, uitnodiging."}},
                             "required": ["titel", "omschrijving"]}},
            "voorstel_tekst": {"type": "string", "description": "Een nette, korte voorsteltekst (6-10 zinnen) die de gebruiker zo aan zijn klant kan sturen, in de ik/wij-vorm van de gebruiker, zonder AI te noemen."},
        },
        "required": ["wat_ze_doen", "ontdekt", "plan", "filmpjes", "voorstel_tekst"],
    },
}

DOELTEKST = {"publiek": "meer publiek / bereik", "klanten": "meer klanten", "verkoop": "meer verkoop",
             "bekend": "bekender worden", "anders": "iets anders"}


def _maak(k_id: int):
    from .ai import _call_tool
    from .methode import met_methode
    with SessionLocal() as db:
        k = db.get(Klant, k_id)
        if not k or k.status != "pending":
            return
        k.status = "processing"
        db.commit()
        try:
            site = lees_website(k.website)
            taal = TAALNAAM.get(k.lang, "Nederlands")
            system = ("Je bent het verkoopteam van Nocturo: een ervaren verkoper met een team (Speurder, Analist, Regisseur, Boekhouder). "
                      "Een gebruiker werkt voor een klant en wil diens doel halen. Schrijf alles in het " + taal + ", in gewone, warme taal, "
                      "spreek de gebruiker aan met 'je'. Baseer je ALLEEN op de websitetekst; verzin geen producten, prijzen of feiten. "
                      "Beloof nooit omzet of aantallen. Maak een logisch funnelplan: eerst gezien worden, dan interesse wekken, dan klant maken.")
            system = met_methode(system, "gebruik de verkoopmethode voor het plan en de filmpjes: herkenbare opening, behoefte wekken, voordelen, bezwaren wegnemen, duidelijke volgende stap.")
            user = (f"Klant: {k.naam}\nWebsite: {site['start']}\nDoel: {DOELTEKST.get(k.doel, k.doel)}\n"
                    f"Extra wens van de gebruiker: {k.wens or '-'}\n\nTekst van de website (per pagina):\n"
                    + json.dumps(site["paginas"], ensure_ascii=False))
            k.plan = json.dumps(_call_tool(system, user, TOOL, max_tokens=5000), ensure_ascii=False)
            k.status = "klaar"
        except Exception as ex:
            print(f"Klant {k_id} mislukt:", ex)
            k.status, k.error = "failed", str(ex)[:400]
        db.commit()


def start(k_id: int):
    threading.Thread(target=_maak, args=(k_id,), daemon=True).start()


def herstel_na_herstart():
    with SessionLocal() as db:
        for k in db.query(Klant).filter(Klant.status.in_(["pending", "processing"])).all():
            k.status = "pending"
        db.commit()
        ids = [k.id for k in db.query(Klant).filter(Klant.status == "pending").all()]
    for i in ids:
        start(i)
