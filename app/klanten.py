"""Voor wie werk je? Het hele kantoor gaat aan het werk voor een klant: website bekijken, doel, voorstel, filmpjes."""
import json
import threading

from .check import lees_website, TAALNAAM
from .models import Klant, SessionLocal

MAX_PER_MAAND = 10   # zoveel analyses per bedrijf per maand (kosten: zoeken + schrijven)
MAX_PLUS = 25        # met het hogere abonnement (Plus)


def deze_maand(db, company_id: int) -> int:
    from datetime import datetime
    nu = datetime.utcnow()
    begin = datetime(nu.year, nu.month, 1)
    return db.query(Klant).filter(Klant.company_id == company_id, Klant.created_at >= begin,
                                  Klant.status != "failed").count()


DOELEN = ["publiek", "klanten", "verkoop", "bekend", "anders"]

KANALEN = ["Instagram","Facebook","TikTok","YouTube","LinkedIn","X","Threads","Reddit","Pinterest","Google","E-mail","Brief","Website"]

TOOL = {
    "name": "voorstel",
    "description": "Volledige verkoopanalyse: profilering, jezelf verkopen, product verkopen, kanalen met kant-en-klare berichten, plan.",
    "input_schema": {
        "type": "object",
        "properties": {
            "wat_ze_doen": {"type": "string", "description": "Wat dit bedrijf/deze persoon verkoopt/doet en voor wie, 2-3 zinnen."},
            "doel": {"type": "object", "description": "Het doel, scherp omschreven op basis van het gekozen doel en de wens van de gebruiker. Alles in het plan werkt hiernaartoe.",
                     "properties": {
                         "omschrijving": {"type": "string", "description": "Wat we willen bereiken, concreet, 1-2 zinnen (geen beloofde aantallen)."},
                         "zo_meten": {"type": "string", "description": "Waaraan je merkt dat het lukt (bijv. meer betalende klanten na de proefweek, meer aanvragen), 1 zin."},
                         "termijn": {"type": "string", "description": "Een redelijke termijn om de eerste resultaten te zien, bijv. 'eerste 4 weken', met korte uitleg."}},
                     "required": ["omschrijving", "zo_meten", "termijn"]},
            "wie_ben_je": {"type": "string", "description": "Profilering: hoe komt het bedrijf nu over, wat maakt ze anders, waarom zou men hen vertrouwen. 3-5 zinnen, eerlijk."},
            "jezelf_verkopen": {"type": "array", "items": {"type": "string"}, "description": "3-5 concrete adviezen om de eigenaar/het bedrijf zelf te verkopen (verhaal, gezicht, vertrouwen, reviews)."},
            "product_verkopen": {"type": "array", "items": {"type": "string"}, "description": "3-5 concrete adviezen om het product/de dienst te verkopen (voor wie, probleem, aanbod, prijs, bezwaren)."},
            "ontdekt": {"type": "array", "items": {"type": "string"}, "description": "3-5 opvallende dingen (goed én beter), ook waar klanten nu weglekken."},
            "kanalen": {"type": "array", "description": "Alle relevante kanalen, ook waar ze nog NIET zijn. 'aanwezig' als je het kanaal vond (website, zoekmachine of opgegeven door de gebruiker); anders 'niet gevonden'. Volgers nooit gokken.",
                        "items": {"type": "object", "properties": {
                            "kanaal": {"type": "string", "enum": KANALEN},
                            "status": {"type": "string", "enum": ["aanwezig", "niet gevonden"], "description": "'aanwezig' als je het kanaal vond via website, zoekmachine of de gebruiker; anders 'niet gevonden'."},
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
                         "uitleg": {"type": "string", "description": "Wat we doen, hoe het bijdraagt aan het doel, en hoe de robot (het programma) het uitvoert. 1-3 zinnen."},
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
        "required": ["wat_ze_doen", "doel", "wie_ben_je", "jezelf_verkopen", "product_verkopen", "ontdekt", "kanalen", "berichten", "plan", "filmpjes", "voorstel_tekst"],
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
            grondig = (k.diepte or "grondig") == "grondig"
            print(f"[klant {k_id}] start analyse {k.website} ({'grondig' if grondig else 'snel'})", flush=True)
            site = lees_website(k.website)
            print(f"[klant {k_id}] website gelezen, {len(site['paginas'])} pagina's", flush=True)
            taal = TAALNAAM.get(k.lang, "Nederlands")
            system = ("Je bent het verkoopteam van Nocturo: een ervaren verkoper met een team (Speurder, Analist, Regisseur, Boekhouder). "
                      "Een gebruiker werkt voor een klant en wil diens doel halen. Schrijf alles in het " + taal + ", in gewone, warme taal, "
                      "spreek de gebruiker aan met 'je'. Baseer je op de websitetekst én op wat je zelf opzoekt met de zoekmachine; verzin geen producten, prijzen of feiten. "
                      "Beloof nooit omzet of aantallen. Kijk breder dan filmpjes: het gaat om de hele verkoopstrategie. Eerst verkoop je jezelf "
                      "(profilering, vertrouwen), daarna je product. Bekijk alle kanalen (social media, Google, mail, brieven) en maak kant-en-klare teksten.")
            doel_taal = TAALNAAM.get(k.doeltaal or "", "") or "de taal van de website (en anders " + taal + ")"
            system += ("\n\nTAAL: alle uitleg en adviezen in het " + taal + ". Maar de velden 'berichten' (tekst én plaatsinstructie blijven: tekst in "
                       "de doeltaal, plaatsinstructie in het " + taal + "), 'filmpjes' en 'voorstel_tekst' schrijf je in: " + doel_taal + ". "
                       "ZOEKEN: gebruik de zoekmachine om het bedrijf op internet op te zoeken: zoek naar hun Instagram, TikTok, YouTube, Facebook, LinkedIn, X, "
                       "Threads, Reddit, reviews (Google, app store, Trustpilot) en 2-3 concurrenten. Een kanaal is 'aanwezig' als je het vindt "
                       "(op de site, via zoeken of door de gebruiker opgegeven). Noem in 'ontdekt' wat je over concurrenten en reviews vond. "
                       "EERLIJKHEID: schrijf berichten altijd eerlijk vanuit de maker/het bedrijf zelf. Doe NOOIT alsof je een klant, winkelier of "
                       "buitenstaander bent en verzin geen eigen ervaringen. Noem geen stapnummers of namen van een verkoopmethode in de tekst.")
            system = met_methode(system, "gebruik de verkoopmethode voor het plan en de filmpjes: herkenbare opening, behoefte wekken, voordelen, bezwaren wegnemen, duidelijke volgende stap.")
            user = (f"Klant: {k.naam}\nWebsite: {site['start']}\nDoel: {DOELTEKST.get(k.doel, k.doel)}\n"
                    f"Extra wens van de gebruiker: {k.wens or '-'}\n"
                    f"Sociale links gevonden op de website: {json.dumps(site.get('socials', {}), ensure_ascii=False) or 'geen'}\n"
                    f"Kanalen die de gebruiker zelf opgaf: {k.kanalen or '-'}\n\nTekst van de website (per pagina):\n"
                    + json.dumps(site["paginas"], ensure_ascii=False))
            try:
                uitslag = _call_tool(system, user, TOOL, max_tokens=14000, zoeken=15 if grondig else 5)
            except Exception as ex:
                # zoekmachine niet beschikbaar: dan zonder zoeken, alleen op de website
                print(f"Klant {k_id}: zoeken mislukt, verder zonder:", ex)
                uitslag = _call_tool(system, user, TOOL, max_tokens=14000)
            print(f"[klant {k_id}] eerste plan klaar", flush=True)
            # Tweede ronde (alleen grondig): een ervaren collega leest het plan na en scherpt het aan.
            try:
                if not grondig:
                    raise StopIteration
                nalees = (system + "\n\nTWEEDE RONDE: je bent de ervaren verkoopleider die het plan van het team naleest. "
                          "Maak het concreter en scherper: haal algemeenheden weg, controleer dat elk advies past bij DIT bedrijf, "
                          "dat de berichten eerlijk en in de juiste taal zijn, en dat de volgorde van het plan logisch is. "
                          "Houd wat goed is; verzin geen nieuwe feiten. Geef het volledige verbeterde plan terug via de tool.")
                uitslag = _call_tool(nalees, user + "\n\nPLAN VAN HET TEAM (om na te lezen en te verbeteren):\n"
                                     + json.dumps(uitslag, ensure_ascii=False), TOOL, max_tokens=14000)
            except StopIteration:
                pass
            except Exception as ex:
                print(f"[klant {k_id}] tweede ronde mislukt, eerste plan blijft:", ex, flush=True)
            k.plan = json.dumps(uitslag, ensure_ascii=False)
            print(f"[klant {k_id}] klaar", flush=True)
            db.commit()
            try:
                stuur_overzicht(db, k, uitslag)
            except Exception as ex:
                print(f"[klant {k_id}] overzichtsmail mislukt:", ex, flush=True)
            k.status = "klaar"
        except Exception as ex:
            print(f"[klant {k_id}] mislukt:", ex, flush=True)
            k.status, k.error = "failed", str(ex)[:400]
        db.commit()


def stuur_overzicht(db, k, plan: dict):
    """Mail met het hele overzicht (HTML, te printen) naar de gebruiker."""
    import os, html, smtplib
    from email.message import EmailMessage
    from email.utils import formataddr
    from .mailer import mail_ready
    from .models import Company
    from . import kantoor as K
    if not mail_ready():
        print(f"[klant {k.id}] geen mail: mail is niet ingesteld", flush=True)
        return
    c = db.get(Company, k.company_id)
    if not c or not c.email or "@" not in c.email:
        return
    L = k.lang or "nl"
    e = lambda t: html.escape(str(t or ""))
    kan = plan.get("kanalen") or []
    aanw = sum(1 for x in kan if x.get("status") == "aanwezig")
    basis = os.environ.get("BASE_URL", "https://nocturo-offerte.onrender.com").rstrip("/")
    link = f"{basis}/klanten/{k.id}"
    def lijst(items):
        return "<ul>" + "".join(f"<li style='margin-bottom:6px'>{e(i)}</li>" for i in items or []) + "</ul>"
    def kop(t):
        return f"<h2 style='font-size:13px;letter-spacing:2px;text-transform:uppercase;color:#6B7884;margin:28px 0 8px'>{e(t)}</h2>"
    stat = lambda n, t: (f"<td style='padding:14px;text-align:center;background:#F7F4EE;border-radius:10px'>"
                         f"<div style='font-size:26px;font-weight:700;color:#18A58C'>{n}</div><div style='font-size:12px;color:#6B7884'>{e(t)}</div></td>")
    h = [f"<div style='font-family:Arial,sans-serif;max-width:680px;margin:auto;color:#1F2A33;line-height:1.5'>",
         f"<p style='color:#18A58C;letter-spacing:3px;font-size:12px'>NOCTURO CONTROL ROOM</p>",
         f"<h1 style='margin:0 0 6px'>{e(k.naam)}</h1><p style='color:#6B7884;margin:0'>{e(k.website)}</p>",
         "<table style='width:100%;border-spacing:8px;margin:18px 0'><tr>",
         stat(f"{aanw}/{len(kan)}", K.k("ml_st_kanalen", L)), stat(len(plan.get("plan") or []), K.k("ml_st_stappen", L)),
         stat(len(plan.get("berichten") or []), K.k("ml_st_berichten", L)), stat(len(plan.get("filmpjes") or []), K.k("ml_st_films", L)),
         "</tr></table>",
         f"<p style='font-size:16px'>{e(plan.get('wat_ze_doen'))}</p>"]
    d = plan.get("doel") or {}
    if d:
        h += [f"<div style='border:2px solid #18A58C;border-radius:12px;padding:14px 16px;margin:18px 0'>"
              f"<div style='font-size:12px;letter-spacing:2px;color:#18A58C;text-transform:uppercase'>{e(K.k('kl_doel_kop', L))}</div>"
              f"<p style='font-size:17px;margin:6px 0'><b>{e(d.get('omschrijving'))}</b></p>"
              f"<p style='margin:4px 0;color:#444'>{e(K.k('kl_doel_meten', L))} {e(d.get('zo_meten'))}</p>"
              f"<p style='margin:4px 0;color:#444'>{e(K.k('kl_doel_termijn', L))} {e(d.get('termijn'))}</p></div>"]
    if plan.get("wie_ben_je"):
        h += [kop(K.k("kl_wie", L)), f"<p>{e(plan['wie_ben_je'])}</p>",
              kop(K.k("kl_zelf", L)), lijst(plan.get("jezelf_verkopen")),
              kop(K.k("kl_product", L)), lijst(plan.get("product_verkopen"))]
    h += [kop(K.k("kl_ontdekt", L)), lijst(plan.get("ontdekt")), kop(K.k("kl_kanalen", L)), "<table style='width:100%;border-collapse:collapse'>"]
    for x in kan:
        kl = "#18A58C" if x.get("status") == "aanwezig" else "#EE8A3C"
        h.append(f"<tr><td style='padding:6px 0;border-top:1px solid #E7E1D6;vertical-align:top;width:120px'><b>{e(x.get('kanaal'))}</b><br>"
                 f"<span style='color:{kl};font-size:12px'>{e(K.k('kl_aanwezig', L) if x.get('status') == 'aanwezig' else K.k('kl_niet', L))}</span></td>"
                 f"<td style='padding:6px 0;border-top:1px solid #E7E1D6;color:#444'>{e(x.get('advies'))}</td></tr>")
    h.append("</table>")
    h.append(kop(K.k("kl_plan", L)) + "<ol>" + "".join(f"<li style='margin-bottom:8px'><b>{e(s.get('stap'))}</b><br>{e(s.get('uitleg'))}</li>" for s in plan.get("plan") or []) + "</ol>")
    if plan.get("berichten"):
        h.append(kop(K.k("kl_berichten", L)))
        for m in plan["berichten"]:
            h.append(f"<div style='border:1px solid #E7E1D6;border-radius:10px;padding:12px;margin-bottom:12px'><b>{e(m.get('kanaal'))}</b> "
                     f"<span style='color:#6B7884'>· {e(m.get('soort'))}</span>"
                     f"<div style='white-space:pre-wrap;background:#FAFAF7;padding:10px;margin:8px 0;border-radius:6px'>{e(m.get('tekst'))}</div>"
                     f"<b style='font-size:13px'>{e(K.k('kl_zoplaats', L))}</b><ol style='color:#555;font-size:13px'>"
                     + "".join(f"<li>{e(st)}</li>" for st in m.get("plaatsen") or []) + "</ol></div>")
    h.append(kop(K.k("kl_films", L)) + "".join(f"<p><b>{e(f.get('titel'))}</b><br><span style='color:#555'>{e(f.get('omschrijving'))}</span></p>" for f in plan.get("filmpjes") or []))
    h.append(kop(K.k("kl_voorstel", L)) + f"<div style='white-space:pre-wrap;background:#FAFAF7;padding:12px;border-radius:6px'>{e(plan.get('voorstel_tekst'))}</div>")
    h.append(f"<p style='margin-top:28px'><a href='{link}' style='background:#18A58C;color:#fff;padding:12px 20px;border-radius:8px;text-decoration:none'>{e(K.k('ml_open', L))}</a></p></div>")
    msg = EmailMessage()
    afzender = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER")
    msg["From"] = formataddr(("Nocturo", afzender))
    msg["To"] = c.email
    msg["Subject"] = K.k("ml_onderwerp", L, n=k.naam)
    msg.set_content(K.k("ml_tekst", L, n=k.naam, link=link))
    msg.add_alternative("".join(h), subtype="html")
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=30) as sm:
        sm.starttls()
        sm.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        sm.send_message(msg)
    print(f"[klant {k.id}] overzicht gemaild naar {c.email}", flush=True)


def start(k_id: int):
    threading.Thread(target=_maak, args=(k_id,), daemon=True).start()


def herstel_na_herstart():
    with SessionLocal() as db:
        from datetime import datetime
        for k in db.query(Klant).filter(Klant.status.in_(["pending", "processing"])).all():
            k.status = "pending"
            k.created_at = datetime.utcnow()   # waakhond telt opnieuw vanaf de herstart
        db.commit()
        ids = [k.id for k in db.query(Klant).filter(Klant.status == "pending").all()]
    for i in ids:
        start(i)
