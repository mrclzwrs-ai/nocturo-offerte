"""Voor wie werk je? Het hele kantoor gaat aan het werk voor een klant: website bekijken, doel, voorstel, filmpjes."""
import json
import threading

from .check import lees_website, TAALNAAM
from .models import Klant, SessionLocal

DOELEN = ["publiek", "klanten", "verkoop", "bekend", "anders"]

KANALEN = ["Instagram","Facebook","TikTok","YouTube","LinkedIn","X","Threads","Reddit","Pinterest","Google","E-mail","Brief","Website"]

TOOL = {
    "name": "voorstel",
    "description": "Volledige verkoopanalyse: profilering, jezelf verkopen, product verkopen, kanalen met kant-en-klare berichten, plan.",
    "input_schema": {
        "type": "object",
        "properties": {
            "wat_ze_doen": {"type": "string", "description": "Wat dit bedrijf/deze persoon verkoopt/doet en voor wie, 2-3 zinnen."},
            "wie_ben_je": {"type": "string", "description": "Profilering: hoe komt het bedrijf nu over, wat maakt ze anders, waarom zou men hen vertrouwen. 3-5 zinnen, eerlijk."},
            "jezelf_verkopen": {"type": "array", "items": {"type": "string"}, "description": "3-5 concrete adviezen om de eigenaar/het bedrijf zelf te verkopen (verhaal, gezicht, vertrouwen, reviews)."},
            "product_verkopen": {"type": "array", "items": {"type": "string"}, "description": "3-5 concrete adviezen om het product/de dienst te verkopen (voor wie, probleem, aanbod, prijs, bezwaren)."},
            "ontdekt": {"type": "array", "items": {"type": "string"}, "description": "3-5 opvallende dingen (goed én beter), ook waar klanten nu weglekken."},
            "kanalen": {"type": "array", "description": "Alle relevante kanalen, ook waar ze nog NIET zijn. Status alleen 'aanwezig' als de link in de gevonden sociale links staat; anders 'niet gevonden'. Volgers nooit gokken.",
                        "items": {"type": "object", "properties": {
                            "kanaal": {"type": "string", "enum": KANALEN},
                            "status": {"type": "string", "enum": ["aanwezig", "niet gevonden"], "description": "'aanwezig' als het kanaal in de gevonden of door de gebruiker opgegeven links staat; anders 'niet gevonden'."},
                            "advies": {"type": "string", "description": "Past dit kanaal en wat te doen, 1-2 zinnen."}},
                            "required": ["kanaal", "status", "advies"]}},
            "berichten": {"type": "array", "description": "4-6 kant-en-klare stukken voor de beste kanalen: geen filmpjes maar tekst (post, verhaal, uitleg, draadje, brief, mail). Reddit: behulpzaam, geen reclame.",
                          "items": {"type": "object", "properties": {
                              "kanaal": {"type": "string", "enum": KANALEN},
                              "soort": {"type": "string", "description": "Bijv. post met foto, verhaal, draadje, brief, mail, uitleg."},
                              "tekst": {"type": "string", "description": "De volledige tekst, klaar om te plakken, met eventuele hashtags."},
                              "plaatsen": {"type": "array", "items": {"type": "string"}, "description": "3-5 korte stappen hoe je dit zelf plaatst op dit kanaal."}},
                              "required": ["kanaal", "soort", "tekst", "plaatsen"]}},
            "plan": {"type": "array", "description": "4-6 stappen in volgorde: eerst jezelf profileren, dan gezien worden, dan interesse, dan klant maken, dan vasthouden.",
                     "items": {"type": "object", "properties": {
                         "stap": {"type": "string", "description": "Korte titel van de stap (3-7 woorden)."},
                         "uitleg": {"type": "string", "description": "Wat we doen en waarom, 1-2 zinnen."},
                         "robot": {"type": "string", "enum": ["speurder", "analist", "regisseur", "boekhouder"],
                                   "description": "speurder=nieuwe klanten zoeken, mails en brieven, analist=onderzoek en teksten, regisseur=filmpjes, boekhouder=offertes."}},
                         "required": ["stap", "uitleg", "robot"]}},
            "filmpjes": {"type": "array", "description": "2-3 ideeën voor korte reclamefilmpjes, als één onderdeel van het plan.",
                         "items": {"type": "object", "properties": {
                             "titel": {"type": "string", "description": "Wat er in beeld komt, kort."},
                             "omschrijving": {"type": "string", "description": "2-3 zinnen voor de voice-over."}},
                             "required": ["titel", "omschrijving"]}},
            "voorstel_tekst": {"type": "string", "description": "Nette voorsteltekst (6-10 zinnen) die de gebruiker zo aan zijn klant kan sturen, in de ik/wij-vorm van de gebruiker, zonder AI te noemen."},
        },
        "required": ["wat_ze_doen", "wie_ben_je", "jezelf_verkopen", "product_verkopen", "ontdekt", "kanalen", "berichten", "plan", "filmpjes", "voorstel_tekst"],
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
                      "Beloof nooit omzet of aantallen. Kijk breder dan filmpjes: het gaat om de hele verkoopstrategie. Eerst verkoop je jezelf "
                      "(profilering, vertrouwen), daarna je product. Bekijk alle kanalen (social media, Google, mail, brieven) en maak kant-en-klare teksten.")
            doel_taal = TAALNAAM.get(k.doeltaal or "", "") or "de taal van de website (en anders " + taal + ")"
            system += ("\n\nTAAL: alle uitleg en adviezen in het " + taal + ". Maar de velden 'berichten' (tekst én plaatsinstructie blijven: tekst in "
                       "de doeltaal, plaatsinstructie in het " + taal + "), 'filmpjes' en 'voorstel_tekst' schrijf je in: " + doel_taal + ". "
                       "EERLIJKHEID: schrijf berichten altijd eerlijk vanuit de maker/het bedrijf zelf. Doe NOOIT alsof je een klant, winkelier of "
                       "buitenstaander bent en verzin geen eigen ervaringen. Noem geen stapnummers of namen van een verkoopmethode in de tekst.")
            system = met_methode(system, "gebruik de verkoopmethode voor het plan en de filmpjes: herkenbare opening, behoefte wekken, voordelen, bezwaren wegnemen, duidelijke volgende stap.")
            user = (f"Klant: {k.naam}\nWebsite: {site['start']}\nDoel: {DOELTEKST.get(k.doel, k.doel)}\n"
                    f"Extra wens van de gebruiker: {k.wens or '-'}\n"
                    f"Sociale links gevonden op de website: {json.dumps(site.get('socials', {}), ensure_ascii=False) or 'geen'}\n"
                    f"Kanalen die de gebruiker zelf opgaf: {k.kanalen or '-'}\n\nTekst van de website (per pagina):\n"
                    + json.dumps(site["paginas"], ensure_ascii=False))
            k.plan = json.dumps(_call_tool(system, user, TOOL, max_tokens=9000), ensure_ascii=False)
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
