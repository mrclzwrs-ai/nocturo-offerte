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
# Video Ads Plus (40 filmpjes per maand) en bijkopen per 10 (27 nov 2026)
PRIJS_PLUS = 59.0
PLUS_PER_MAAND = 40
PRIJS_EXTRA = 25.0
EXTRA_PAKKET = 10

APPS = [
    {"key": "search", "name": "Search & Analyze", "price": 12.5, "url": "/search"},
    {"key": "offerte", "name": "Offerte", "price": 12.5, "url": "/offertes"},
    {"key": "video", "name": "Video Ads", "price": 29.0, "url": "/video"},
    {"key": "pling", "name": "Pling", "price": 12.5, "url": "https://nocturoapps.com/pling/"},
]
APP_KEYS = [a["key"] for a in APPS] + ["controlroom", "videoplus"]
# Welke apps een klant in zijn kantoor ziet, naar wie hij verkoopt
DOELGROEP_APPS = {
    "b2b": ["search", "offerte", "video"],
    "b2c": ["video", "pling"],
}
# Vriendenaccount: alles staat aan en het kost niets (alleen Marcel zet dit aan via /beheer)
VRIEND = "vriend"


def is_vriend(subs: dict) -> bool:
    v = subs.get(VRIEND)
    st = v.status if hasattr(v, "status") else v
    return st == "actief"
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
    if key == "video" and subs.get("videoplus") and subs["videoplus"].status == "actief":
        return "actief"
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
    if is_vriend(subs):
        return 0.0
    if subs.get("controlroom") and subs["controlroom"].status == "actief":
        return PRIJS_CONTROLROOM
    tot = 0.0
    plus = bool(subs.get("videoplus") and subs["videoplus"].status == "actief")
    for a in APPS:
        if app_status(company, subs, a["key"]) == "actief":
            tot += PRIJS_PLUS if (a["key"] == "video" and plus) else a["price"]
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
    "admin_acc": ["Beheerder: alle apps", "Administrator: all apps", "Administrator: alle Apps", "Administrateur : toutes les applis", "Administrador: todas las apps"],
    "total": ["Totaal per maand", "Total per month", "Gesamt pro Monat", "Total par mois", "Total al mes"],
    "nothing_yet": ["Nog geen gehuurde apps.", "No rented apps yet.", "Noch keine gemieteten Apps.",
                    "Pas encore d'applis louées.", "Aún no hay apps alquiladas."],
    "pay_note": ["Betalen regelen we voorlopig persoonlijk met je. Online betalen komt binnenkort.",
                 "For now we arrange payment with you personally. Online payment is coming soon.",
                 "Die Zahlung regeln wir vorerst persönlich mit Ihnen. Online-Zahlung folgt bald.",
                 "Pour l'instant, nous réglons le paiement avec vous personnellement. Le paiement en ligne arrive bientôt.",
                 "Por ahora acordamos el pago contigo personalmente. El pago en línea llegará pronto."],
    "friend": ["Vriendenaccount", "Friends account", "Freundeskonto", "Compte ami", "Cuenta de amigo"],
    "friend_note": ["Alle apps staan gratis voor je aan. Veel plezier ermee!",
                    "All apps are switched on for you, free of charge. Enjoy!",
                    "Alle Apps sind kostenlos für Sie aktiviert. Viel Spaß damit!",
                    "Toutes les applis sont activées gratuitement pour vous. Profitez-en !",
                    "Todas las apps están activadas gratis para ti. ¡Disfrútalas!"],
    "free": ["Gratis", "Free", "Kostenlos", "Gratuit", "Gratis"],
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
    "v_left": ["Deze maand nog {n} van de {m} filmpjes over", "{n} of {m} videos left this month", "Diesen Monat noch {n} von {m} Videos übrig", "Encore {n} vidéos sur {m} ce mois-ci", "Te quedan {n} de {m} vídeos este mes"],
    "v_left_trial": ["Proef: nog {n} van {m} gratis filmpjes", "Trial: {n} of {m} free videos left", "Test: noch {n} von {m} Gratis-Videos", "Essai : encore {n} vidéos gratuites sur {m}", "Prueba: quedan {n} de {m} vídeos gratis"],
    "v_title": ["Naam van het product", "Product name", "Produktname", "Nom du produit", "Nombre del producto"],
    "v_price": ["Prijs (€)", "Price (€)", "Preis (€)", "Prix (€)", "Precio (€)"],
    "v_desc": ["Korte omschrijving", "Short description", "Kurze Beschreibung", "Courte description", "Descripción breve"],
    "v_photos": ["Foto's (1 tot 4) · tip: 3 of 4 foto's geven het mooiste filmpje", "Photos (1 to 4) · tip: 3 or 4 photos make the best video",
                 "Fotos (1 bis 4) · Tipp: 3 oder 4 Fotos ergeben das schönste Video", "Photos (1 à 4) · astuce : 3 ou 4 photos donnent la plus belle vidéo",
                 "Fotos (1 a 4) · consejo: 3 o 4 fotos dan el mejor vídeo"],
    "v_lang": ["Taal van de stem", "Voice language", "Sprache der Stimme", "Langue de la voix", "Idioma de la voz"],
    "v_make": ["Maak het filmpje", "Make the video", "Video erstellen", "Créer la vidéo", "Crear el vídeo"],
    "v_mine": ["Mijn filmpjes", "My videos", "Meine Videos", "Mes vidéos", "Mis vídeos"],
    "v_none": ["Nog geen filmpjes.", "No videos yet.", "Noch keine Videos.", "Pas encore de vidéos.", "Aún no hay vídeos."],
    "v_busy": ["Wordt gemaakt… (ongeveer een minuut)", "Being made… (about a minute)", "Wird erstellt… (etwa eine Minute)", "En cours… (environ une minute)", "Creándose… (aprox. un minuto)"],
    "v_failed": ["Dit filmpje is mislukt.", "This video failed.", "Dieses Video ist fehlgeschlagen.", "Cette vidéo a échoué.", "Este vídeo ha fallado."],
    "naar_site": ["Terug naar nocturoapps.com", "Back to nocturoapps.com", "Zurück zu nocturoapps.com", "Retour à nocturoapps.com", "Volver a nocturoapps.com"],
    "wc_naam": ["Company Analyzer", "Company Analyzer", "Company Analyzer", "Company Analyzer", "Company Analyzer"],
    "wc_inbegrepen": ["Inbegrepen bij Video Ads", "Included with Video Ads", "In Video Ads enthalten", "Inclus avec Video Ads", "Incluido con Video Ads"],
    "wc_kort": ["Laat een website analyseren: verbeterpunten en een verkoopplan voor particulieren, met ideeën voor filmpjes.",
                "Have a website analysed: improvement tips and a sales plan for consumers, with video ideas.",
                "Lassen Sie eine Website analysieren: Verbesserungen und ein Verkaufsplan für Privatkunden, mit Video-Ideen.",
                "Faites analyser un site : pistes d'amélioration et plan de vente pour particuliers, avec des idées de vidéos.",
                "Analiza una web: mejoras y un plan de ventas para particulares, con ideas de vídeos."],
    "wc_url": ["Je website", "Your website", "Ihre Website", "Votre site", "Tu web"],
    "wc_start": ["Bekijk mijn website", "Check my website", "Meine Website prüfen", "Analyser mon site", "Revisar mi web"],
    "wc_gestart": ["Je website wordt bekeken. Dat duurt ongeveer een minuut.", "Your website is being checked. This takes about a minute.",
                   "Ihre Website wird geprüft. Das dauert etwa eine Minute.", "Votre site est en cours d'analyse. Cela prend environ une minute.",
                   "Estamos revisando tu web. Tarda aproximadamente un minuto."],
    "wc_bezig": ["Je website wordt bekeken… (ongeveer een minuut)", "Checking your website… (about a minute)",
                 "Website wird geprüft… (etwa eine Minute)", "Analyse en cours… (environ une minute)", "Revisando tu web… (aprox. un minuto)"],
    "wc_mislukt": ["De check is mislukt. Klopt het adres van je website?", "The check failed. Is your website address correct?",
                   "Die Prüfung ist fehlgeschlagen. Stimmt die Adresse?", "L'analyse a échoué. L'adresse est-elle correcte ?",
                   "La revisión ha fallado. ¿Es correcta la dirección?"],
    "wc_over": ["Deze maand nog {n} van de {m} checks over", "{n} of {m} checks left this month", "Diesen Monat noch {n} von {m} Prüfungen übrig", "Encore {n} analyses sur {m} ce mois-ci", "Te quedan {n} de {m} revisiones este mes"],
    "wc_op": ["Je checks zijn op. Huur Video Ads voor 4 checks per maand.", "No checks left. Rent Video Ads for 4 checks a month.",
              "Keine Prüfungen mehr. Mieten Sie Video Ads für 4 Prüfungen pro Monat.", "Plus d'analyses. Louez Video Ads pour 4 analyses par mois.",
              "No te quedan revisiones. Alquila Video Ads para 4 al mes."],
    "wc_samenvatting": ["Wat valt op", "At a glance", "Auf einen Blick", "En bref", "De un vistazo"],
    "wc_sterk": ["Wat al goed is", "What's already good", "Was schon gut ist", "Ce qui est déjà bien", "Lo que ya está bien"],
    "wc_beter": ["Verbeterpunten", "Improvements", "Verbesserungen", "Améliorations", "Mejoras"],
    "wc_belang_hoog": ["Belangrijk", "Important", "Wichtig", "Important", "Importante"],
    "wc_belang_middel": ["Goed om te doen", "Worth doing", "Sinnvoll", "Utile", "Conviene"],
    "wc_belang_laag": ["Als je tijd hebt", "If you have time", "Wenn Zeit bleibt", "Si vous avez le temps", "Si tienes tiempo"],
    "wc_plan": ["Je verkoopplan", "Your sales plan", "Ihr Verkaufsplan", "Votre plan de vente", "Tu plan de ventas"],
    "wc_kanalen": ["Waar je particulieren bereikt", "Where to reach consumers", "Wo Sie Privatkunden erreichen", "Où toucher les particuliers", "Dónde llegar a particulares"],
    "wc_producten": ["Hiermee begin je", "Start with these", "Damit beginnen Sie", "Commencez par ceux-ci", "Empieza con estos"],
    "wc_weken": ["Plan voor 4 weken", "4-week plan", "4-Wochen-Plan", "Plan sur 4 semaines", "Plan de 4 semanas"],
    "wc_week": ["Week {n}", "Week {n}", "Woche {n}", "Semaine {n}", "Semana {n}"],
    "wc_maak": ["Maak dit filmpje", "Make this video", "Dieses Video erstellen", "Créer cette vidéo", "Crear este vídeo"],
    "wc_verwachting": ["Wat je kunt verwachten", "What to expect", "Was Sie erwarten können", "À quoi s'attendre", "Qué esperar"],
    "wc_eerder": ["Eerdere checks", "Earlier checks", "Frühere Prüfungen", "Analyses précédentes", "Revisiones anteriores"],
    "wc_advies": ["Dit is advies op basis van de tekst op je website, geen garantie op resultaat.", "This is advice based on the text on your website, not a guarantee of results.",
                  "Dies ist eine Empfehlung auf Basis des Website-Textes, keine Ergebnisgarantie.", "Ce sont des conseils basés sur le texte de votre site, sans garantie de résultat.",
                  "Es un consejo basado en el texto de tu web, no una garantía de resultados."],
    "dg_kop": ["Eerst even kennismaken", "Let's get to know you", "Kurz kennenlernen", "Faisons connaissance", "Primero, conozcámonos"],
    "dg_vraag": ["Aan wie verkoop jij?", "Who do you sell to?", "An wen verkaufen Sie?", "À qui vendez-vous ?", "¿A quién vendes?"],
    "dg_uitleg": ["Dan laat je kantoor alleen de hulp zien die bij jou past. Je kunt het later altijd nog veranderen.",
                  "Your office will then only show the help that fits you. You can always change it later.",
                  "Ihr Büro zeigt dann nur die Hilfe, die zu Ihnen passt. Sie können das später jederzeit ändern.",
                  "Votre bureau n'affichera alors que l'aide qui vous convient. Vous pourrez toujours changer plus tard.",
                  "Tu oficina mostrará solo la ayuda que te conviene. Siempre puedes cambiarlo más tarde."],
    "dg_b2b": ["Ik verkoop aan bedrijven", "I sell to businesses", "Ich verkaufe an Unternehmen", "Je vends aux entreprises", "Vendo a empresas"],
    "dg_b2b_uitleg": ["Nieuwe zakelijke klanten vinden en mailen, offertes maken en reclamefilmpjes.",
                      "Find and email new business customers, make quotes and promo videos.",
                      "Neue Geschäftskunden finden und anschreiben, Angebote und Werbevideos erstellen.",
                      "Trouver et contacter de nouveaux clients professionnels, faire des devis et des vidéos.",
                      "Encontrar y escribir a nuevos clientes empresa, hacer presupuestos y vídeos."],
    "dg_b2c": ["Ik verkoop aan particulieren", "I sell to consumers", "Ich verkaufe an Privatkunden", "Je vends aux particuliers", "Vendo a particulares"],
    "dg_b2c_uitleg": ["Meer klanten in je winkel of webshop: reclamefilmpjes en aanbiedingen voor mensen in de buurt.",
                      "More customers in your shop or webshop: promo videos and offers for people nearby.",
                      "Mehr Kunden im Laden oder Webshop: Werbevideos und Angebote für Leute in der Nähe.",
                      "Plus de clients en boutique ou en ligne : vidéos promo et offres pour les gens du quartier.",
                      "Más clientes en tu tienda u online: vídeos promocionales y ofertas para la gente cercana."],
    "dg_nu": ["Je verkoopt aan {w}", "You sell to {w}", "Sie verkaufen an {w}", "Vous vendez aux {w}", "Vendes a {w}"],
    "dg_w_b2b": ["bedrijven (B2B)", "businesses (B2B)", "Unternehmen (B2B)", "entreprises (B2B)", "empresas (B2B)"],
    "dg_w_b2c": ["particulieren (B2C)", "consumers (B2C)", "Privatkunden (B2C)", "particuliers (B2C)", "particulares (B2C)"],
    "dg_wijzig": ["wijzigen", "change", "ändern", "modifier", "cambiar"],
    "dg_binnenkort": ["Binnenkort in je kantoor: je eigen website laten nakijken, met verbeterpunten en een verkoopplan voor particulieren.",
                      "Coming soon to your office: have your own website checked, with improvement tips and a sales plan for consumers.",
                      "Demnächst in Ihrem Büro: Ihre eigene Website prüfen lassen, mit Verbesserungen und einem Verkaufsplan für Privatkunden.",
                      "Bientôt dans votre bureau : faire vérifier votre site, avec des pistes d'amélioration et un plan de vente pour particuliers.",
                      "Pronto en tu oficina: revisar tu propia web, con mejoras y un plan de ventas para particulares."],
    "pw_vergeten": ["Wachtwoord vergeten?", "Forgot your password?", "Passwort vergessen?", "Mot de passe oublié ?", "¿Olvidaste tu contraseña?"],
    "pw_uitleg": ["Vul je e-mailadres in. Je krijgt een mail met een linkje om een nieuw wachtwoord te kiezen.", "Enter your email address. You will receive an email with a link to choose a new password.", "Geben Sie Ihre E-Mail-Adresse ein. Sie erhalten eine E-Mail mit einem Link, um ein neues Passwort zu wählen.", "Saisissez votre adresse e-mail. Vous recevrez un lien pour choisir un nouveau mot de passe.", "Escribe tu correo. Recibirás un enlace para elegir una contraseña nueva."],
    "pw_stuur": ["Stuur mij een linkje", "Send me a link", "Link senden", "M'envoyer un lien", "Envíame un enlace"],
    "pw_kijk_mail": ["Kijk in je mail", "Check your email", "Schauen Sie in Ihre E-Mails", "Consultez vos e-mails", "Revisa tu correo"],
    "pw_verstuurd": ["Als dit adres bij ons bekend is, staat er binnen een paar minuten een mail met een linkje in je postvak. Kijk ook even bij de ongewenste mail. Het linkje werkt 2 uur.", "If this address is known to us, an email with a link will arrive within a few minutes. Also check your spam folder. The link works for 2 hours.", "Wenn diese Adresse bei uns bekannt ist, erhalten Sie in wenigen Minuten eine E-Mail mit einem Link. Schauen Sie auch im Spam-Ordner nach. Der Link gilt 2 Stunden.", "Si cette adresse est connue, un e-mail avec un lien arrivera dans quelques minutes. Vérifiez aussi vos spams. Le lien est valable 2 heures.", "Si conocemos esta dirección, recibirás en unos minutos un correo con un enlace. Mira también en spam. El enlace funciona 2 horas."],
    "pw_geen_mail": ["Het versturen van de mail lukt op dit moment niet. Stuur ons even een berichtje, dan helpen we je meteen:", "Sending the email is not possible right now. Send us a message and we will help you right away:", "Der Versand der E-Mail ist gerade nicht möglich. Schreiben Sie uns, wir helfen sofort:", "L'envoi de l'e-mail est impossible pour le moment. Écrivez-nous, nous vous aidons tout de suite :", "Ahora mismo no se puede enviar el correo. Escríbenos y te ayudamos enseguida:"],
    "pw_kies": ["Kies een nieuw wachtwoord", "Choose a new password", "Neues Passwort wählen", "Choisissez un nouveau mot de passe", "Elige una contraseña nueva"],
    "pw_nieuw": ["Nieuw wachtwoord (minstens 8 tekens)", "New password (at least 8 characters)", "Neues Passwort (mindestens 8 Zeichen)", "Nouveau mot de passe (au moins 8 caractères)", "Contraseña nueva (mínimo 8 caracteres)"],
    "pw_nog_eens": ["Nog een keer hetzelfde wachtwoord", "Same password again", "Dasselbe Passwort noch einmal", "Le même mot de passe encore une fois", "La misma contraseña otra vez"],
    "pw_opslaan": ["Opslaan en inloggen", "Save and log in", "Speichern und anmelden", "Enregistrer et se connecter", "Guardar y entrar"],
    "pw_kort": ["Kies een wachtwoord van minstens 8 tekens.", "Choose a password of at least 8 characters.", "Wählen Sie ein Passwort mit mindestens 8 Zeichen.", "Choisissez un mot de passe d'au moins 8 caractères.", "Elige una contraseña de al menos 8 caracteres."],
    "pw_anders": ["De twee wachtwoorden zijn niet hetzelfde.", "The two passwords are not the same.", "Die beiden Passwörter stimmen nicht überein.", "Les deux mots de passe ne sont pas identiques.", "Las dos contraseñas no coinciden."],
    "pw_klaar": ["Je nieuwe wachtwoord is opgeslagen.", "Your new password has been saved.", "Ihr neues Passwort wurde gespeichert.", "Votre nouveau mot de passe est enregistré.", "Tu nueva contraseña se ha guardado."],
    "pw_verlopen": ["Dit linkje werkt niet meer. Het is verlopen of al gebruikt. Vraag gewoon een nieuw linkje aan.", "This link no longer works. It has expired or was already used. Just request a new link.", "Dieser Link funktioniert nicht mehr. Er ist abgelaufen oder wurde schon benutzt. Fordern Sie einfach einen neuen an.", "Ce lien ne fonctionne plus. Il a expiré ou a déjà été utilisé. Demandez simplement un nouveau lien.", "Este enlace ya no funciona. Ha caducado o ya se usó. Pide uno nuevo."],
    "pw_mail_onderwerp": ["Je nieuwe wachtwoord voor Nocturo", "Your new password for Nocturo", "Ihr neues Passwort für Nocturo", "Votre nouveau mot de passe Nocturo", "Tu nueva contraseña de Nocturo"],
    "pw_mail_tekst": ["Hallo {naam},\n\nJe hebt gevraagd om een nieuw wachtwoord voor je Nocturo-kantoor. Klik op dit linkje om er een te kiezen:\n\n{link}\n\nHet linkje werkt 2 uur. Heb je dit niet zelf gevraagd? Dan kun je deze mail gewoon negeren.\n\nGroet,\nNocturo",
                      "Hello {naam},\n\nYou asked for a new password for your Nocturo office. Click this link to choose one:\n\n{link}\n\nThe link works for 2 hours. Didn't ask for this? Then just ignore this email.\n\nRegards,\nNocturo",
                      "Hallo {naam},\n\nSie haben ein neues Passwort für Ihr Nocturo-Büro angefordert. Klicken Sie auf diesen Link, um eines zu wählen:\n\n{link}\n\nDer Link gilt 2 Stunden. Haben Sie das nicht angefordert? Dann ignorieren Sie diese E-Mail einfach.\n\nGrüße,\nNocturo",
                      "Bonjour {naam},\n\nVous avez demandé un nouveau mot de passe pour votre bureau Nocturo. Cliquez sur ce lien pour le choisir :\n\n{link}\n\nLe lien est valable 2 heures. Vous n'avez rien demandé ? Ignorez simplement cet e-mail.\n\nCordialement,\nNocturo",
                      "Hola {naam},\n\nHas pedido una contraseña nueva para tu oficina Nocturo. Pulsa este enlace para elegirla:\n\n{link}\n\nEl enlace funciona 2 horas. ¿No lo has pedido tú? Ignora este correo.\n\nSaludos,\nNocturo"],
    "faq": ["Vragen", "Questions", "Fragen", "Questions", "Preguntas"],
    "faq_titel": ["Vragen en antwoorden", "Questions and answers", "Fragen und Antworten", "Questions et réponses", "Preguntas y respuestas"],
    "faq_meer": ["Staat je vraag er niet bij? Mail ons:", "Question not listed? Email us:", "Ihre Frage ist nicht dabei? Schreiben Sie uns:", "Votre question n'y est pas ? Écrivez-nous :", "¿No está tu pregunta? Escríbenos:"],
    "v_shop": ["Bedrijfsnaam in het filmpje (maak je het voor een klant? vul dan de naam van de klant in)",
               "Business name in the video (making it for a client? enter the client's name)",
               "Firmenname im Video (für einen Kunden? dann den Namen des Kunden eintragen)",
               "Nom de l'entreprise dans la vidéo (pour un client ? indiquez le nom du client)",
               "Nombre del negocio en el vídeo (¿es para un cliente? pon el nombre del cliente)"],
    "v_site": ["Website", "Website", "Website", "Site web", "Web"],
    "v_music": ["Muziek", "Music", "Musik", "Musique", "Música"],
    "v_music_auto": ["Laat het kantoor kiezen", "Let the office choose", "Das Büro wählen lassen", "Laisser le bureau choisir", "Que elija la oficina"],
    "v_music_auto_uitleg": ["Een muziekje dat past bij de stijl, steeds een ander.", "Music that fits the style, a different one each time.",
                            "Passende Musik zum Stil, jedes Mal eine andere.", "Une musique adaptée au style, chaque fois différente.",
                            "Música que encaja con el estilo, cada vez una distinta."],
    "v_music_play": ["Luister", "Listen", "Anhören", "Écouter", "Escuchar"],
    "mz_stoer_duur": ["Stoer en duur", "Bold and luxurious", "Kraftvoll und edel", "Audacieux et luxueux", "Potente y lujoso"],
    "mz_stoer_energiek": ["Stoer en energiek", "Bold and energetic", "Kraftvoll und energisch", "Audacieux et énergique", "Potente y enérgico"],
    "mz_fris_vrolijk": ["Fris en vrolijk", "Fresh and cheerful", "Frisch und fröhlich", "Frais et joyeux", "Fresco y alegre"],
    "mz_rechten": ["Al onze muziek is eigen werk, speciaal gemaakt voor Nocturo. Je mag hem zonder zorgen gebruiken in je filmpjes, ook als je ermee verdient.",
                   "All our music is our own work, made especially for Nocturo. You can use it in your videos without worry, even commercially.",
                   "Unsere gesamte Musik ist eigene Arbeit, speziell für Nocturo gemacht. Sie können sie unbesorgt in Ihren Videos verwenden, auch kommerziell.",
                   "Toute notre musique est une création originale pour Nocturo. Vous pouvez l'utiliser sans souci dans vos vidéos, même à des fins commerciales.",
                   "Toda nuestra música es obra propia, hecha especialmente para Nocturo. Puedes usarla sin preocupaciones en tus vídeos, también con fines comerciales."],
    "mz_opmaat": ["Wil je een eigen nummer, met een tekst over jouw zaak? Stuur ons een berichtje waar het over moet gaan, dan maken wij het gratis voor je:",
                  "Want your own song, with lyrics about your business? Send us a note about what it should be about and we'll make it for you, free:",
                  "Möchten Sie einen eigenen Song mit einem Text über Ihr Geschäft? Schreiben Sie uns, worum es gehen soll, und wir machen ihn kostenlos für Sie:",
                  "Vous voulez votre propre chanson, avec des paroles sur votre entreprise ? Dites-nous de quoi elle doit parler, nous la créons gratuitement :",
                  "¿Quieres una canción propia, con letra sobre tu negocio? Escríbenos de qué debe tratar y la hacemos gratis para ti:"],
    "mz_opmaat_onderwerp": ["Nummer op maat", "Custom song", "Song nach Maß", "Chanson sur mesure", "Canción a medida"],
    "mz_spiritueel": ["Spiritueel en rustig", "Spiritual and calm", "Spirituell und ruhig", "Spirituel et apaisant", "Espiritual y tranquilo"],
    "mz_rustig_warm": ["Rustig en warm", "Calm and warm", "Ruhig und warm", "Calme et chaleureux", "Tranquilo y cálido"],
    "v_style": ["Stijl van het filmpje", "Video style", "Stil des Videos", "Style de la vidéo", "Estilo del vídeo"],
    "st_foto": ["Foto vol", "Full photo", "Vollbild-Foto", "Photo pleine", "Foto completa"],
    "st_foto_uitleg": ["Je foto over het hele scherm, grote stoere letters.", "Your photo fills the screen, big bold letters.", "Ihr Foto füllt den Bildschirm, große kräftige Schrift.", "Votre photo plein écran, grandes lettres affirmées.", "Tu foto a pantalla completa, letras grandes y llamativas."],
    "st_luxe": ["Luxe", "Luxury", "Luxus", "Luxe", "Lujo"],
    "st_luxe_uitleg": ["Zwart met goud, sierlijke letters.", "Black and gold, elegant lettering.", "Schwarz und Gold, elegante Schrift.", "Noir et or, lettres élégantes.", "Negro y dorado, letras elegantes."],
    "st_licht": ["Strak licht", "Clean light", "Hell und klar", "Clair et épuré", "Claro y limpio"],
    "st_licht_uitleg": ["Lichte achtergrond, product op een witte kaart.", "Light background, product on a white card.", "Heller Hintergrund, Produkt auf weißer Karte.", "Fond clair, produit sur une carte blanche.", "Fondo claro, producto sobre una tarjeta blanca."],
    "v_length_hint": ["Tip: hoe meer je over het product vertelt, hoe langer en rijker het filmpje wordt (tot ongeveer 30 seconden).", "Tip: the more you tell about the product, the longer and richer the video (up to about 30 seconds).", "Tipp: Je mehr Sie über das Produkt erzählen, desto länger und reicher wird das Video (bis etwa 30 Sekunden).", "Astuce : plus vous décrivez le produit, plus la vidéo est longue et riche (jusqu'à environ 30 secondes).", "Consejo: cuanto más cuentes del producto, más largo y completo será el vídeo (hasta unos 30 segundos)."],
    "v_retry": ["Opnieuw proberen", "Try again", "Erneut versuchen", "Réessayer", "Reintentar"],
    "v_download": ["⤓ Download", "⤓ Download", "⤓ Herunterladen", "⤓ Télécharger", "⤓ Descargar"],
    "v_watch": ["Bekijk", "Watch", "Ansehen", "Voir", "Ver"],
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


TEKSTEN.update({
    "v_meer_t": ["Meer filmpjes nodig?", "Need more videos?", "Mehr Videos nötig?", "Besoin de plus de vidéos ?", "¿Necesitas más vídeos?"],
    "v_op_t": ["Je filmpjes voor deze maand zijn op. Wat wil je doen?", "You've used this month's videos. What would you like to do?",
               "Ihre Videos für diesen Monat sind aufgebraucht. Was möchten Sie tun?", "Vos vidéos du mois sont épuisées. Que voulez-vous faire ?",
               "Has usado los vídeos de este mes. ¿Qué quieres hacer?"],
    "v_extra_btn": ["10 extra filmpjes · € 25 eenmalig", "10 extra videos · € 25 one-off", "10 Extra-Videos · € 25 einmalig",
                    "10 vidéos en plus · 25 € une fois", "10 vídeos extra · 25 € una vez"],
    "v_plus_btn": ["Video Ads Plus · 40 per maand voor € 59", "Video Ads Plus · 40 a month for € 59", "Video Ads Plus · 40 pro Monat für € 59",
                   "Video Ads Plus · 40 par mois pour 59 €", "Video Ads Plus · 40 al mes por 59 €"],
    "v_meer_hint": ["Met Plus betaal je per filmpje het minst. Extra filmpjes gelden voor deze maand.",
                    "Plus gives you the lowest price per video. Extra videos are for this month.",
                    "Mit Plus zahlen Sie pro Video am wenigsten. Extra-Videos gelten für diesen Monat.",
                    "Avec Plus, chaque vidéo vous coûte le moins cher. Les vidéos en plus valent pour ce mois-ci.",
                    "Con Plus pagas menos por vídeo. Los vídeos extra valen para este mes."],
    "v_plus_aan": ["Je hebt Video Ads Plus: 40 filmpjes per maand.", "You have Video Ads Plus: 40 videos a month.",
                   "Sie haben Video Ads Plus: 40 Videos pro Monat.", "Vous avez Video Ads Plus : 40 vidéos par mois.",
                   "Tienes Video Ads Plus: 40 vídeos al mes."],
    "v_plus_wacht": ["Je aanvraag voor Plus is binnen. We zetten het aan zodra de betaling rond is.",
                     "Your Plus request is in. We'll switch it on as soon as the payment is done.",
                     "Ihre Plus-Anfrage ist da. Wir schalten es frei, sobald die Zahlung erledigt ist.",
                     "Votre demande Plus est reçue. Nous l'activons dès que le paiement est fait.",
                     "Tu solicitud de Plus ha llegado. La activamos en cuanto se complete el pago."],
})

TEKSTEN.update({
    "v_voice": ["Stem", "Voice", "Stimme", "Voix", "Voz"],
    "stem_std": ["Moedertaalstem", "Native voice", "Muttersprachliche Stimme", "Voix native", "Voz nativa"],
    "stem_std_uitleg": ["De vaste stem voor de gekozen taal", "The standard voice for the chosen language", "Die Standardstimme für die gewählte Sprache",
                        "La voix standard de la langue choisie", "La voz estándar del idioma elegido"],
    "stem_man": ["Mannenstem", "Male voice", "Männerstimme", "Voix d'homme", "Voz masculina"],
    "stem_man_uitleg": ["Warm en krachtig", "Warm and strong", "Warm und kräftig", "Chaleureuse et forte", "Cálida y potente"],
    "stem_vrouw": ["Vrouwenstem", "Female voice", "Frauenstimme", "Voix de femme", "Voz femenina"],
    "stem_vrouw_uitleg": ["Helder en rustig", "Clear and calm", "Klar und ruhig", "Claire et calme", "Clara y tranquila"],
})

# Robots: elke app heeft zijn eigen collega (zelfde robots als in de promofilm)
TEKSTEN.update({
    "rb_n_search": ["De Speurder", "The Scout", "Die Spürnase", "L'Éclaireur", "El Rastreador"],
    "rb_n_check": ["De Analist", "The Analyst", "Der Analyst", "L'Analyste", "El Analista"],
    "rb_n_video": ["De Regisseur", "The Director", "Der Regisseur", "Le Réalisateur", "El Director"],
    "rb_n_offerte": ["De Boekhouder", "The Bookkeeper", "Der Buchhalter", "Le Comptable", "El Contable"],
    "rb_n_pling": ["Pling", "Pling", "Pling", "Pling", "Pling"],
    "rb_hi_search": ["Hoi, ik ben de Speurder. Ik zoek bedrijven die bij jou passen en schrijf ze een persoonlijke brief.",
                     "Hi, I'm the Scout. I find businesses that suit you and write them a personal letter.",
                     "Hallo, ich bin die Spürnase. Ich finde passende Unternehmen und schreibe ihnen einen persönlichen Brief.",
                     "Bonjour, je suis l'Éclaireur. Je trouve des entreprises qui vous correspondent et je leur écris une lettre personnelle.",
                     "Hola, soy el Rastreador. Busco empresas que encajan contigo y les escribo una carta personal."],
    "rb_hi_check": ["Hoi, ik ben de Analist. Geef me een website, dan bekijk ik hem door de ogen van een klant.",
                    "Hi, I'm the Analyst. Give me a website and I'll look at it through the eyes of a customer.",
                    "Hallo, ich bin der Analyst. Geben Sie mir eine Website, dann schaue ich sie mit den Augen eines Kunden an.",
                    "Bonjour, je suis l'Analyste. Donnez-moi un site, je le regarde avec les yeux d'un client.",
                    "Hola, soy el Analista. Dame una web y la miro con los ojos de un cliente."],
    "rb_hi_video": ["Hoi, ik ben de Regisseur. Vertel me over je product, dan maak ik er een filmpje van.",
                    "Hi, I'm the Director. Tell me about your product and I'll turn it into a video.",
                    "Hallo, ich bin der Regisseur. Erzählen Sie mir von Ihrem Produkt, dann mache ich ein Video daraus.",
                    "Bonjour, je suis le Réalisateur. Parlez-moi de votre produit, j'en fais une vidéo.",
                    "Hola, soy el Director. Cuéntame de tu producto y hago un vídeo con él."],
    "rb_hi_offerte": ["Hoi, ik ben de Boekhouder. Vertel me wat je klant wil, dan maak ik er een nette offerte van.",
                      "Hi, I'm the Bookkeeper. Tell me what your customer wants and I'll make a neat quote.",
                      "Hallo, ich bin der Buchhalter. Sagen Sie mir, was Ihr Kunde möchte, dann mache ich ein sauberes Angebot.",
                      "Bonjour, je suis le Comptable. Dites-moi ce que veut votre client, j'en fais un devis soigné.",
                      "Hola, soy el Contable. Dime qué quiere tu cliente y hago un presupuesto bien hecho."],
    "rb_hi_pling": ["Hoi, ik ben Pling. Ik breng jouw aanbiedingen bij mensen in de buurt.",
                    "Hi, I'm Pling. I bring your deals to people nearby.",
                    "Hallo, ich bin Pling. Ich bringe Ihre Angebote zu Menschen in der Nähe.",
                    "Bonjour, je suis Pling. J'apporte vos offres aux gens du quartier.",
                    "Hola, soy Pling. Llevo tus ofertas a la gente de tu barrio."],
})

TEKSTEN.update({
    "v_soort_vraag": ["1. Wat voor filmpje wil je?", "1. What kind of video do you want?", "1. Was für ein Video möchten Sie?",
                      "1. Quel type de vidéo voulez-vous ?", "1. ¿Qué tipo de vídeo quieres?"],
    "v_soort": ["Soort filmpje", "Type of video", "Art des Videos", "Type de vidéo", "Tipo de vídeo"],
    "v_gewoon": ["Gewoon filmpje", "Standard video", "Standard-Video", "Vidéo standard", "Vídeo estándar"],
    "v_gewoon_uitleg": ["Je foto's met mooie overgangen · kost 1 filmpje", "Your photos with smooth transitions · costs 1 video",
                        "Ihre Fotos mit schönen Übergängen · kostet 1 Video", "Vos photos avec de belles transitions · coûte 1 vidéo",
                        "Tus fotos con transiciones bonitas · cuesta 1 vídeo"],
    "v_echt": ["Echte video ✨", "Real video ✨", "Echtes Video ✨", "Vraie vidéo ✨", "Vídeo real ✨"],
    "v_echt_uitleg": ["Je foto's gaan echt bewegen, als in een film · kost {n} filmpjes · duurt een paar minuten",
                      "Your photos really come to life, like in a film · costs {n} videos · takes a few minutes",
                      "Ihre Fotos bewegen sich wirklich, wie im Film · kostet {n} Videos · dauert ein paar Minuten",
                      "Vos photos s'animent vraiment, comme au cinéma · coûte {n} vidéos · prend quelques minutes",
                      "Tus fotos cobran vida de verdad, como en una película · cuesta {n} vídeos · tarda unos minutos"],
    "v_echt_te_weinig": ["Voor een Echte video heb je {n} filmpjes tegoed nodig. Koop er 10 bij of kies Plus.",
                         "A Real video needs {n} videos from your balance. Buy 10 extra or choose Plus.",
                         "Für ein Echtes Video brauchen Sie noch {n} Videos. Kaufen Sie 10 dazu oder wählen Sie Plus.",
                         "Une Vraie vidéo nécessite {n} vidéos. Achetez-en 10 de plus ou choisissez Plus.",
                         "Un Vídeo real necesita {n} vídeos. Compra 10 más o elige Plus."],
    "v_started_echt": ["Je Echte video wordt gemaakt. Dit duurt een paar minuten; je mag dit scherm gewoon openlaten of later terugkomen.",
                       "Your Real video is being made. This takes a few minutes; you can keep this screen open or come back later.",
                       "Ihr Echtes Video wird erstellt. Das dauert ein paar Minuten; Sie können diese Seite offen lassen oder später zurückkommen.",
                       "Votre Vraie vidéo est en cours. Cela prend quelques minutes ; vous pouvez laisser cet écran ouvert ou revenir plus tard.",
                       "Tu Vídeo real se está creando. Tarda unos minutos; puedes dejar esta pantalla abierta o volver más tarde."],
    "v_beweging": ["Wat moet er bewegen? (mag leeg blijven)", "What should move? (optional)", "Was soll sich bewegen? (optional)",
                   "Qu'est-ce qui doit bouger ? (facultatif)", "¿Qué debe moverse? (opcional)"],
    "v_beweging_uitleg": ["Vertel in je eigen woorden wat je wilt zien. Bijvoorbeeld: er komt een lekkere damp uit de hete koffie · het mannetje loopt van links naar rechts · de jurk wappert in de wind · er vallen kruiden in het potje. Laat je het leeg, dan bedenken wij zelf iets moois dat bij je product past.",
                          "Describe in your own words what you want to see. For example: steam rises from the hot coffee · the little man walks from left to right · the dress flutters in the wind · spices fall into the jar. Leave it empty and we'll come up with something beautiful that suits your product.",
                          "Beschreiben Sie in eigenen Worten, was Sie sehen möchten. Zum Beispiel: Dampf steigt aus dem heißen Kaffee · das Männchen läuft von links nach rechts · das Kleid flattert im Wind · Gewürze fallen ins Glas. Lassen Sie es leer, dann denken wir uns selbst etwas Schönes aus.",
                          "Décrivez avec vos mots ce que vous voulez voir. Par exemple : de la vapeur s'élève du café chaud · le petit bonhomme marche de gauche à droite · la robe flotte au vent · des épices tombent dans le pot. Laissez vide et nous imaginerons nous-mêmes quelque chose de beau.",
                          "Describe con tus palabras lo que quieres ver. Por ejemplo: sale vapor del café caliente · el muñequito camina de izquierda a derecha · el vestido ondea al viento · caen especias en el bote. Déjalo vacío y nosotros pensamos algo bonito que encaje con tu producto."],
    "v_busy_echt": ["Je foto's worden tot leven gewekt… dit duurt een paar minuten.", "Bringing your photos to life… this takes a few minutes.",
                    "Ihre Fotos werden zum Leben erweckt… das dauert ein paar Minuten.", "Vos photos prennent vie… cela prend quelques minutes.",
                    "Dando vida a tus fotos… tarda unos minutos."],
})

def k(key: str, lang: str, **kw) -> str:
    vals = TEKSTEN.get(key)
    if not vals:
        return key
    s = vals[_IDX.get(lang, 0)]
    return s.format(**kw) if kw else s
