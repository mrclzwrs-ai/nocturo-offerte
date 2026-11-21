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
    {"key": "search", "name": "Search & Analyze", "price": 12.5, "url": "/search"},
    {"key": "offerte", "name": "Offerte", "price": 12.5, "url": "/offertes"},
    {"key": "video", "name": "Video Ads", "price": 29.0, "url": "/video"},
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
        if (company.paid_until and company.paid_until > now) or getattr(company, "_extra_toegang", False):
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


TEKSTEN.update({
    "back_office": ["← Terug naar je kantoor", "← Back to your office", "← Zurück zum Büro", "← Retour au bureau", "← Volver a tu oficina"],
    "try": ["Probeer", "Try it", "Ausprobieren", "Essayer", "Probar"],
    "no_access": ["Deze app staat nog niet aan voor je account. Huur hem in je kantoor.",
                  "This app is not switched on for your account yet. Rent it in your office.",
                  "Diese App ist für Ihr Konto noch nicht aktiviert. Mieten Sie sie in Ihrem Büro.",
                  "Cette appli n'est pas encore activée pour votre compte. Louez-la dans votre bureau.",
                  "Esta app aún no está activada para tu cuenta. Alquílala en tu oficina."],
    # Video Ads
    "v_new": ["Nieuw filmpje", "New video", "Neues Video", "Nouvelle vidéo", "Nuevo vídeo"],
    "v_left": ["Nog {n} van {m} filmpjes", "{n} of {m} videos left", "Noch {n} von {m} Videos", "Encore {n} vidéos sur {m}", "Quedan {n} de {m} vídeos"],
    "v_left_trial": ["Proef: nog {n} van {m} gratis filmpjes", "Trial: {n} of {m} free videos left", "Test: noch {n} von {m} Gratis-Videos", "Essai : encore {n} vidéos gratuites sur {m}", "Prueba: quedan {n} de {m} vídeos gratis"],
    "v_title": ["Naam van het product", "Product name", "Produktname", "Nom du produit", "Nombre del producto"],
    "v_price": ["Prijs (€)", "Price (€)", "Preis (€)", "Prix (€)", "Precio (€)"],
    "v_desc": ["Korte omschrijving", "Short description", "Kurze Beschreibung", "Courte description", "Descripción breve"],
    "v_photos": ["Foto's (1 tot 4)", "Photos (1 to 4)", "Fotos (1 bis 4)", "Photos (1 à 4)", "Fotos (1 a 4)"],
    "v_lang": ["Taal van de stem", "Voice language", "Sprache der Stimme", "Langue de la voix", "Idioma de la voz"],
    "v_make": ["Maak het filmpje", "Make the video", "Video erstellen", "Créer la vidéo", "Crear el vídeo"],
    "v_mine": ["Mijn filmpjes", "My videos", "Meine Videos", "Mes vidéos", "Mis vídeos"],
    "v_none": ["Nog geen filmpjes.", "No videos yet.", "Noch keine Videos.", "Pas encore de vidéos.", "Aún no hay vídeos."],
    "v_busy": ["Wordt gemaakt… (ongeveer een minuut)", "Being made… (about a minute)", "Wird erstellt… (etwa eine Minute)", "En cours… (environ une minute)", "Creándose… (aprox. un minuto)"],
    "v_failed": ["Mislukt, probeer het opnieuw", "Failed, please try again", "Fehlgeschlagen, bitte erneut versuchen", "Échec, réessayez", "Ha fallado, inténtalo de nuevo"],
    "v_watch": ["Bekijk en download", "Watch and download", "Ansehen und herunterladen", "Voir et télécharger", "Ver y descargar"],
    "v_limit": ["Je filmpjes voor deze maand zijn op.", "You have used all your videos for this month.", "Ihre Videos für diesen Monat sind aufgebraucht.", "Vous avez utilisé toutes vos vidéos ce mois-ci.", "Has usado todos tus vídeos de este mes."],
    "v_trial_over": ["Je gratis proeffilmpjes zijn op. Huur Video Ads in je kantoor om verder te gaan.", "Your free trial videos are used up. Rent Video Ads in your office to continue.", "Ihre Gratis-Testvideos sind aufgebraucht. Mieten Sie Video Ads in Ihrem Büro.", "Vos vidéos d'essai sont épuisées. Louez Video Ads dans votre bureau.", "Tus vídeos de prueba se han agotado. Alquila Video Ads en tu oficina."],
    "v_need_photo": ["Voeg minstens één foto toe.", "Add at least one photo.", "Fügen Sie mindestens ein Foto hinzu.", "Ajoutez au moins une photo.", "Añade al menos una foto."],
    "v_not_ready": ["Video Ads wordt op dit moment ingeschakeld. Probeer het straks opnieuw.", "Video Ads is being switched on right now. Please try again later.", "Video Ads wird gerade aktiviert. Bitte später erneut versuchen.", "Video Ads est en cours d'activation. Réessayez plus tard.", "Video Ads se está activando. Inténtalo más tarde."],
    "v_started": ["Je filmpje wordt gemaakt. Het verschijnt hieronder.", "Your video is being made. It will appear below.", "Ihr Video wird erstellt. Es erscheint unten.", "Votre vidéo est en cours. Elle apparaîtra ci-dessous.", "Tu vídeo se está creando. Aparecerá abajo."],
    # Search & Analyze
    "s_settings": ["Instellingen", "Settings", "Einstellungen", "Paramètres", "Ajustes"],
    "s_offer": ["Wat bied je aan, en waarom past het bij webwinkels?", "What do you offer, and why does it suit online shops?", "Was bieten Sie an, und warum passt es zu Onlineshops?", "Que proposez-vous, et pourquoi cela convient-il aux boutiques en ligne ?", "¿Qué ofreces y por qué encaja con las tiendas online?"],
    "s_offer_hint": ["Een paar zinnen in je eigen woorden. Hieruit schrijft de Analyzer elke mail.", "A few sentences in your own words. The Analyzer writes every email from this.", "Ein paar Sätze in Ihren eigenen Worten. Daraus schreibt der Analyzer jede E-Mail.", "Quelques phrases avec vos mots. L'Analyzer écrit chaque e-mail à partir de cela.", "Unas frases con tus palabras. El Analyzer escribe cada correo a partir de esto."],
    "s_link": ["Je website (komt in de mail)", "Your website (goes in the email)", "Ihre Website (kommt in die E-Mail)", "Votre site (dans l'e-mail)", "Tu web (va en el correo)"],
    "s_sender": ["Naam onder de mail", "Name under the email", "Name unter der E-Mail", "Nom sous l'e-mail", "Nombre bajo el correo"],
    "s_smtp_user": ["Je e-mailadres (afzender)", "Your email address (sender)", "Ihre E-Mail-Adresse (Absender)", "Votre adresse e-mail (expéditeur)", "Tu correo (remitente)"],
    "s_smtp_pass": ["App-wachtwoord van je mail", "App password of your email", "App-Passwort Ihrer E-Mail", "Mot de passe d'application", "Contraseña de aplicación"],
    "s_smtp_hint": ["Bij Gmail: Google-account › Beveiliging › App-wachtwoorden (16 tekens). Leeg laten = niet wijzigen.", "For Gmail: Google Account › Security › App passwords (16 characters). Leave empty to keep it.", "Bei Gmail: Google-Konto › Sicherheit › App-Passwörter (16 Zeichen). Leer lassen = nicht ändern.", "Pour Gmail : Compte Google › Sécurité › Mots de passe d'application (16 caractères). Vide = inchangé.", "En Gmail: Cuenta de Google › Seguridad › Contraseñas de aplicaciones (16 caracteres). Vacío = sin cambios."],
    "s_server": ["Mailserver en poort", "Mail server and port", "Mailserver und Port", "Serveur et port", "Servidor y puerto"],
    "s_countries": ["Landen", "Countries", "Länder", "Pays", "Países"],
    "s_niche": ["Soort winkels (leeg = alles)", "Type of shops (empty = all)", "Art der Shops (leer = alle)", "Type de boutiques (vide = toutes)", "Tipo de tiendas (vacío = todas)"],
    "s_per_day": ["Mails per werkdag (max. 10)", "Emails per working day (max. 10)", "E-Mails pro Werktag (max. 10)", "E-mails par jour ouvré (max. 10)", "Correos por día laborable (máx. 10)"],
    "s_on": ["Elke werkdag automatisch versturen", "Send automatically every working day", "Jeden Werktag automatisch senden", "Envoyer automatiquement chaque jour ouvré", "Enviar automáticamente cada día laborable"],
    "s_save": ["Opslaan", "Save", "Speichern", "Enregistrer", "Guardar"],
    "s_saved": ["Opgeslagen.", "Saved.", "Gespeichert.", "Enregistré.", "Guardado."],
    "s_test": ["Stuur een testmail naar mezelf", "Send a test email to myself", "Testmail an mich senden", "M'envoyer un e-mail de test", "Enviarme un correo de prueba"],
    "s_test_ok": ["Testmail verstuurd. Kijk in je inbox.", "Test email sent. Check your inbox.", "Testmail gesendet. Schauen Sie in Ihr Postfach.", "E-mail de test envoyé. Vérifiez votre boîte.", "Correo de prueba enviado. Revisa tu bandeja."],
    "s_test_fail": ["Testmail mislukt: {m}", "Test email failed: {m}", "Testmail fehlgeschlagen: {m}", "Échec de l'e-mail de test : {m}", "Falló el correo de prueba: {m}"],
    "s_run": ["Nu een ronde draaien", "Run a round now", "Jetzt eine Runde starten", "Lancer une tournée maintenant", "Hacer una ronda ahora"],
    "s_running": ["De Analyzer is aan het werk. Dit duurt een paar minuten; ververs de pagina straks.", "The Analyzer is working. This takes a few minutes; refresh the page shortly.", "Der Analyzer arbeitet. Das dauert ein paar Minuten; laden Sie die Seite gleich neu.", "L'Analyzer travaille. Cela prend quelques minutes ; actualisez la page.", "El Analyzer está trabajando. Tarda unos minutos; actualiza la página."],
    "s_incomplete": ["Vul eerst je aanbod, e-mailadres en app-wachtwoord in.", "First fill in your offer, email address and app password.", "Füllen Sie zuerst Angebot, E-Mail-Adresse und App-Passwort aus.", "Renseignez d'abord votre offre, votre e-mail et le mot de passe d'application.", "Primero rellena tu oferta, tu correo y la contraseña de aplicación."],
    "s_log": ["Logboek", "Logbook", "Logbuch", "Journal", "Registro"],
    "s_sent_total": ["{n} winkels gemaild", "{n} shops emailed", "{n} Shops angeschrieben", "{n} boutiques contactées", "{n} tiendas contactadas"],
    "s_last": ["Laatste ronde: {d}", "Last round: {d}", "Letzte Runde: {d}", "Dernière tournée : {d}", "Última ronda: {d}"],
    "s_none": ["Nog geen winkels gemaild.", "No shops emailed yet.", "Noch keine Shops angeschrieben.", "Aucune boutique contactée.", "Aún no se ha contactado ninguna tienda."],
    "s_failed": ["mislukt", "failed", "fehlgeschlagen", "échec", "fallido"],
})

_IDX = {"nl": 0, "en": 1, "de": 2, "fr": 3, "es": 4}


def k(key: str, lang: str, **kw) -> str:
    vals = TEKSTEN.get(key)
    if not vals:
        return key
    s = vals[_IDX.get(lang, 0)]
    return s.format(**kw) if kw else s
