"""Search & Analyze voor klanten van Nocturo.

Per klant: elke werkdag één ronde. De app zoekt webwinkels in de gekozen landen, bekijkt hun
website en laat Claude een persoonlijke mail schrijven over het aanbod van de klant. De mail
gaat vanaf het eigen e-mailadres van de klant (SMTP, bijv. Gmail met een app-wachtwoord).
Een winkel krijgt van dezelfde klant nooit twee keer een mail.
"""
import base64
import hashlib
import os
import threading
import traceback
from datetime import datetime

import requests
from cryptography.fernet import Fernet

from ..models import SALead, SAProfiel, SessionLocal
from . import detective as det
from . import outreach_core as oc

LIJST_URL = "https://raw.githubusercontent.com/mrclzwrs-ai/Shopify-outreach-app/main/shopify_winkels.txt"
LIJST_PAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shopify_winkels.txt")
MAX_PER_DAG = 10
LANDEN = ["NL", "BE", "DE", "UK", "US", "ES"]

TAALNAAM = {"NL": "Nederlands", "EN": "Engels", "DE": "Duits", "ES": "Spaans"}

SYSTEEM = """Je schrijft namens een ondernemer een eerste, persoonlijke mail aan een webwinkel.
Wat de ondernemer aanbiedt staat hieronder bij AANBOD. De methode is "Verkopen blijft mensenwerk":
- Schrijf als een mens tegen een mens: kort, warm, eerlijk, geen reclametaal, geen overdreven complimenten.
- Laat zien dat je echt naar DEZE winkel hebt gekeken: noem één of twee concrete dingen van hun site.
  Verzin nooit iets wat niet in de tekst staat.
- Maak één duidelijke koppeling tussen hun winkel en het aanbod.
- Geen kritiek op hun website. Geen druk, geen nep-urgentie, geen beloftes over omzet.
- Eindig met een lichte, open vraag of uitnodiging.
Regels:
- Geen namen van medewerkers of eigenaren en geen privégegevens. Spreek de winkel aan.
- Maximaal ongeveer 120 woorden in de mail zelf. Schrijf in de gevraagde taal; het rapport altijd in het Nederlands.
- Zet de link precies zoals gegeven in de mail. Eindig met een groet en de naam van de afzender.
Antwoord ALLEEN met geldige JSON:
{"rapport": "3 tot 5 korte zinnen in het Nederlands", "onderwerp": "korte, persoonlijke onderwerpregel", "mail": "de volledige mailtekst"}"""


# ---------- wachtwoord versleutelen ----------
def _fernet():
    geheim = os.environ.get("SECRET_KEY") or "dev"
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("sa:" + geheim).encode()).digest()))


def versleutel(pw: str) -> str:
    return _fernet().encrypt(pw.encode()).decode() if pw else ""


def ontsleutel(tok: str) -> str:
    try:
        return _fernet().decrypt(tok.encode()).decode() if tok else ""
    except Exception:
        return ""


# ---------- de winkellijst ----------
def lijst_bijwerken():
    """Haalt de wekelijks bijgewerkte lijst met Shopify-winkels op (hooguit één keer per dag)."""
    try:
        if os.path.exists(LIJST_PAD) and (datetime.now().timestamp() - os.path.getmtime(LIJST_PAD)) < 86400:
            return
        r = requests.get(LIJST_URL, timeout=60)
        if r.ok and len(r.text) > 1000:
            with open(LIJST_PAD, "w", encoding="utf-8") as f:
                f.write(r.text)
    except Exception as ex:
        print("Winkellijst ophalen mislukt:", ex)


# ---------- de mail ----------
def schrijf_mail(lead, profiel, ai=None):
    """Geeft (onderwerp, tekst, rapport) of None als het niet lukt."""
    tekst, reden = det.verzamel_winkeltekst(lead["website"])
    if tekst is None:
        return None
    taal = lead.get("taal", "EN")
    naam = lead.get("winkelnaam") or lead.get("domein")
    if oc.is_rare_naam(naam):
        naam = lead.get("domein")
    prompt = (f"AANBOD van de ondernemer:\n{profiel.aanbod}\n\nWinkel: {naam}\nWebsite: {lead['website']}\n"
              f"Taal van de mail: {TAALNAAM.get(taal, 'Engels')}\nAfzender (naam onder de mail): {profiel.afzender}\n"
              f"Link: {profiel.link}\n\nOpenbare tekst van hun website:\n\"\"\"\n{tekst}\n\"\"\"")
    data = None
    for _ in range(2):
        try:
            antwoord = ai(prompt) if ai else _vraag(prompt)
            data = det._lees_json(antwoord)
            break
        except Exception:
            continue
    if not data:
        return None
    mail = data["mail"].strip()
    if profiel.link and profiel.link not in mail:
        mail += f"\n\n{profiel.link}"
    afmeld = oc.AFMELD_ZIN.get(taal, oc.AFMELD_ZIN["EN"]) + "\n" + oc.afmeld_link(profiel.smtp_user)
    return data["onderwerp"].strip(), f"{mail}\n\n--\n{afmeld}", data["rapport"].strip()


def _vraag(prompt):
    from ..ai import MODEL, _client
    msg = _client().messages.create(model=MODEL, max_tokens=2000, system=SYSTEEM,
                                    messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def testmail(profiel) -> tuple[bool, str]:
    return oc.verstuur_mail(profiel.smtp_user, ontsleutel(profiel.smtp_pass), profiel.afzender or profiel.smtp_user,
                            profiel.smtp_user, "Nocturo Search & Analyze: testmail",
                            "Dit is een testmail. Je mailinstellingen werken.", profiel.smtp_server,
                            profiel.smtp_port, afmeldbaar=False)


# ---------- één ronde ----------
_BEZIG = set()
_SLOT = threading.Lock()


def bezig(company_id) -> bool:
    return company_id in _BEZIG


def ronde(company_id, zoek=None, ai=None, verstuur=None, log=print):
    """Eén ronde voor één klant. zoek/ai/verstuur kunnen voor tests vervangen worden."""
    with _SLOT:
        if company_id in _BEZIG:
            return
        _BEZIG.add(company_id)
    try:
        with SessionLocal() as db:
            p = db.query(SAProfiel).filter(SAProfiel.company_id == company_id).first()
            if not p or not p.smtp_user or not p.smtp_pass or not p.aanbod:
                return
            p.laatste_ronde = datetime.utcnow()
            p.melding = ""
            db.commit()
            bekend = db.query(SALead).filter(SALead.company_id == company_id).all()
            bekende_domeinen = {x.domein for x in bekend}
            bekende_adressen = {x.email for x in bekend}
            landen = [x for x in (p.landen or "").split(",") if x in LANDEN] or ["NL", "BE"]
            aantal = max(1, min(MAX_PER_DAG, p.per_dag or MAX_PER_DAG))
            if zoek is None:
                lijst_bijwerken()
                leads, _, _, fout = oc.zoek_leads_shopifylijst(
                    max_leads=aantal, landen=tuple(landen), niche=p.niche or "",
                    bekende_adressen=bekende_adressen, bekende_domeinen=bekende_domeinen, log=log)
            else:
                leads, fout = zoek(aantal), None
            if fout:
                p.melding = fout
                db.commit()
                return
            wachtwoord = ontsleutel(p.smtp_pass)
            verstuur = verstuur or oc.verstuur_mail
            for lead in leads[:aantal]:
                mail = schrijf_mail(lead, p, ai=ai)
                if not mail:
                    continue
                onderwerp, tekst, rapport = mail
                ok, melding = verstuur(p.smtp_user, wachtwoord, p.afzender or p.smtp_user, lead["email"],
                                       onderwerp, tekst, p.smtp_server, p.smtp_port)
                db.add(SALead(company_id=company_id, domein=lead.get("domein", ""), email=lead["email"],
                              winkelnaam=lead.get("winkelnaam", ""), website=lead.get("website", ""),
                              land=lead.get("markt", ""), onderwerp=onderwerp, tekst=tekst, rapport=rapport,
                              status="verstuurd" if ok else "mislukt", fout="" if ok else str(melding)[:300]))
                db.commit()
                if not ok and "auth" in str(melding).lower():
                    p.melding = "Inloggen bij je mail lukte niet. Kijk je e-mailadres en app-wachtwoord na."
                    db.commit()
                    break
    except Exception:
        traceback.print_exc()
    finally:
        _BEZIG.discard(company_id)


def ronde_op_achtergrond(company_id):
    threading.Thread(target=ronde, args=(company_id,), daemon=True).start()


def dagelijkse_ronde(actieve_ids):
    """Start voor elke klant met een actief abonnement de ronde van vandaag (één keer per dag, werkdagen)."""
    nu = datetime.utcnow()
    if nu.weekday() >= 5:
        return 0
    gestart = 0
    with SessionLocal() as db:
        for p in db.query(SAProfiel).filter(SAProfiel.aan == True).all():  # noqa: E712
            if p.company_id not in actieve_ids:
                continue
            if p.laatste_ronde and p.laatste_ronde.date() == nu.date():
                continue
            ronde_op_achtergrond(p.company_id)
            gestart += 1
    return gestart
