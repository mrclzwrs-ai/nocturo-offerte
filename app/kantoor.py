"""Het Nocturo-kantoor: één account, alle Nocturo-apps op één plek.

Een account (Company) logt één keer in en ziet hier welke apps hij huurt.
Offerte gebruikt zijn eigen proef/betaald-velden op Company; de andere apps
staan in de tabel nocturo_apps (AppSub). Betalen gaat voorlopig persoonlijk:
Marcel zet een app op 'actief' via /beheer.

Prijzen (21 nov 2026): Search & Analyze, Offerte en Pling €12,50 per maand,
Video Ads €29 per maand (15 filmpjes), de hele control room €49 per maand.
Pling: het eerste jaar gratis tijdens de proef in Oost-Nederland.
"""
from datetime import datetime

PRIJS_CONTROLROOM = 49.0

APPS = [
    {"key": "search", "name": "Search & Analyze", "price": 12.5, "url": None},
    {"key": "offerte", "name": "Offerte", "price": 12.5, "url": "/offertes"},
    {"key": "video", "name": "Video Ads", "price": 29.0, "url": None},
    {"key": "pling", "name": "Pling", "price": 12.5, "url": "https://nocturoapps.com/pling/"},
]
APP_KEYS = [a["key"] for a in APPS] + ["controlroom"]
PRIJS_LOS = sum(a["price"] for a in APPS)


def app_status(company, subs: dict, key: str) -> str:
    """Geeft: actief / proef / verlopen / aangevraagd / pilot / geen."""
    if key == "offerte":
        if company.is_demo:
            return "proef"
        now = datetime.utcnow()
        if company.paid_until and company.paid_until > now:
            return "actief"
        if company.trial_ends and company.trial_ends > now:
            return "proef"
        sub = subs.get("offerte")
        return "aangevraagd" if sub and sub.status == "aangevraagd" else "verlopen"
    sub = subs.get(key)
    if sub and sub.status in ("actief", "aangevraagd"):
        return sub.status
    if key == "pling":
        return "pilot"
    return "geen"


def kaarten(company, subs: dict):
    uit = []
    for a in APPS:
        st = app_status(company, subs, a["key"])
        uit.append({**a, "status": st})
    return uit


def maandbedrag(company, subs: dict) -> float:
    if subs.get("controlroom") and subs["controlroom"].status == "actief":
        return PRIJS_CONTROLROOM
    tot = 0.0
    for a in APPS:
        if app_status(company, subs, a["key"]) == "actief":
            tot += a["price"]
    return tot


# Teksten in vijf talen: nl, en, de, fr, es
TEKSTEN = {
    "office": ["Mijn kantoor", "My office", "Mein Büro", "Mon bureau", "Mi oficina"],
    "office_title": [
        "Je verkoopteam staat klaar.", "Your sales team is ready.", "Ihr Vertriebsteam ist bereit.",
        "Votre équipe de vente est prête.", "Tu equipo de ventas está listo."],
    "apps_active": ["{n} van {m} apps actief", "{n} of {m} apps active", "{n} von {m} Apps aktiv",
                    "{n} sur {m} applis actives", "{n} de {m} apps activas"],
    "st_actief": ["Gehuurd", "Rented", "Gemietet", "Louée", "Alquilada"],
    "st_proef": ["Proef · nog {d} dagen", "Trial · {d} days left", "Test · noch {d} Tage",
                 "Essai · encore {d} jours", "Prueba · quedan {d} días"],
    "st_verlopen": ["Proef verlopen", "Trial ended", "Test abgelaufen", "Essai terminé", "Prueba terminada"],
    "st_aangevraagd": ["Aangevraagd", "Requested", "Angefragt", "Demandée", "Solicitada"],
    "st_geen": ["Niet gehuurd", "Not rented", "Nicht gemietet", "Non louée", "No alquilada"],
    "st_pilot": ["Proef Oost-Nederland", "Pilot East Netherlands", "Pilotprojekt Ost-Niederlande",
                 "Pilote est des Pays-Bas", "Piloto este de Países Bajos"],
    "open": ["Open", "Open", "Öffnen", "Ouvrir", "Abrir"],
    "rent": ["Huur deze app", "Rent this app", "Diese App mieten", "Louer cette appli", "Alquilar esta app"],
    "join_pilot": ["Doe mee met de proef", "Join the pilot", "Am Pilotprojekt teilnehmen",
                   "Rejoindre le pilote", "Únete al piloto"],
    "soon": ["Wordt klaargezet voor klanten", "Being set up for customers", "Wird für Kunden vorbereitet",
             "En préparation pour les clients", "Preparándose para clientes"],
    "requested_note": ["We nemen contact met je op.", "We will contact you.", "Wir melden uns bei Ihnen.",
                       "Nous vous contacterons.", "Nos pondremos en contacto contigo."],
    "per_month": ["per maand", "per month", "pro Monat", "par mois", "al mes"],
    "videos15": ["15 filmpjes", "15 videos", "15 Videos", "15 vidéos", "15 vídeos"],
    "pling_price": ["Eerste jaar gratis · daarna {p} per maand", "First year free · then {p} per month",
                    "Erstes Jahr kostenlos · danach {p} pro Monat", "Première année gratuite · puis {p} par mois",
                    "Primer año gratis · después {p} al mes"],
    "control_title": ["De hele control room", "The whole control room", "Der ganze Control Room",
                      "Toute la control room", "Toda la sala de control"],
    "control_text": ["Alle Nocturo-apps naast elkaar, voor één vast bedrag:",
                     "All Nocturo apps side by side, for one fixed price:",
                     "Alle Nocturo-Apps nebeneinander, zu einem festen Preis:",
                     "Toutes les applis Nocturo côte à côte, pour un prix fixe :",
                     "Todas las apps de Nocturo juntas, por un precio fijo:"],
    "loose": ["los {p}", "separately {p}", "einzeln {p}", "séparément {p}", "por separado {p}"],
    "rent_all": ["Alles huren", "Rent everything", "Alles mieten", "Tout louer", "Alquilar todo"],
    "my_account": ["Mijn account", "My account", "Mein Konto", "Mon compte", "Mi cuenta"],
    "my_sub": ["Mijn abonnement", "My subscription", "Mein Abo", "Mon abonnement", "Mi suscripción"],
    "company": ["Zaak", "Business", "Firma", "Entreprise", "Empresa"],
    "total": ["Totaal per maand", "Total per month", "Gesamt pro Monat", "Total par mois", "Total al mes"],
    "nothing_yet": ["Nog geen gehuurde apps.", "No rented apps yet.", "Noch keine gemieteten Apps.",
                    "Pas encore d'applis louées.", "Aún no hay apps alquiladas."],
    "pay_note": ["Betalen regelen we voorlopig persoonlijk met je. Online betalen komt binnenkort.",
                 "For now we arrange payment with you personally. Online payment is coming soon.",
                 "Die Zahlung regeln wir vorerst persönlich mit Ihnen. Online-Zahlung folgt bald.",
                 "Pour l'instant, nous réglons le paiement avec vous personnellement. Le paiement en ligne arrive bientôt.",
                 "Por ahora acordamos el pago contigo personalmente. El pago en línea llegará pronto."],
    "edit_details": ["Gegevens wijzigen", "Edit details", "Daten ändern", "Modifier les données", "Editar datos"],
    "request_ok": ["Je aanvraag is binnen. We nemen snel contact met je op.",
                   "Your request has been received. We will contact you soon.",
                   "Ihre Anfrage ist eingegangen. Wir melden uns bald.",
                   "Votre demande a bien été reçue. Nous vous contacterons bientôt.",
                   "Hemos recibido tu solicitud. Te contactaremos pronto."],
    "tagline": ["Your wingman in sales"] * 5,
    "desc_search": [
        "Vindt winkels, bekijkt hun website en schrijft elke werkdag een persoonlijke mail.",
        "Finds shops, studies their website and writes a personal email every working day.",
        "Findet Shops, prüft ihre Website und schreibt jeden Werktag eine persönliche E-Mail.",
        "Trouve des boutiques, étudie leur site et rédige chaque jour ouvré un e-mail personnel.",
        "Encuentra tiendas, estudia su web y escribe cada día laborable un correo personal."],
    "desc_offerte": [
        "Spreek in wat de klant wil, en binnen een minuut staat er een nette offerte klaar.",
        "Dictate what the customer wants, and a neat quote is ready within a minute.",
        "Diktieren Sie, was der Kunde möchte, und in einer Minute steht ein sauberes Angebot bereit.",
        "Dictez ce que veut le client, et un devis soigné est prêt en une minute.",
        "Dicta lo que quiere el cliente y en un minuto tienes un presupuesto listo."],
    "desc_video": [
        "Maakt van je producten korte reclamefilmpjes voor TikTok, Instagram en YouTube.",
        "Turns your products into short ad videos for TikTok, Instagram and YouTube.",
        "Macht aus Ihren Produkten kurze Werbevideos für TikTok, Instagram und YouTube.",
        "Transforme vos produits en courtes vidéos publicitaires pour TikTok, Instagram et YouTube.",
        "Convierte tus productos en vídeos publicitarios cortos para TikTok, Instagram y YouTube."],
    "desc_pling": [
        "Iets over of een plek vrij? Eén tik, en mensen in de buurt krijgen een seintje.",
        "Something left over or a free slot? One tap, and people nearby get a ping.",
        "Etwas übrig oder ein Platz frei? Ein Tipp, und Leute in der Nähe bekommen ein Signal.",
        "Quelque chose en trop ou une place libre ? Un geste, et les gens à proximité reçoivent une alerte.",
        "¿Te sobra algo o tienes un hueco libre? Un toque y la gente cercana recibe un aviso."],
}

_IDX = {"nl": 0, "en": 1, "de": 2, "fr": 3, "es": 4}


def k(key: str, lang: str, **kw) -> str:
    vals = TEKSTEN.get(key)
    if not vals:
        return key
    s = vals[_IDX.get(lang, 0)]
    return s.format(**kw) if kw else s
