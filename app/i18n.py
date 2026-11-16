"""Vertalingen voor Nocturo Offerte: het scherm (UI) en het offertedocument (DOC).

Volgorde in elke lijst: nl, en, de, fr, es.
"""

LANGS = ["nl", "en", "de", "fr", "es"]
LANG_NAMES = {"nl": "Nederlands", "en": "English", "de": "Deutsch", "fr": "Français", "es": "Español"}

_UI = {
    "app_name": ["Offerte", "Quote", "Angebot", "Devis", "Presupuesto"],
    "tagline": [
        "Vertel wat de klant wil en krijg binnen een paar minuten een duidelijke, overtuigende offerte.",
        "Tell it what the customer wants and get a clear, convincing quote in minutes.",
        "Sagen Sie, was der Kunde möchte, und erhalten Sie in wenigen Minuten ein klares, überzeugendes Angebot.",
        "Dites ce que veut le client et obtenez un devis clair et convaincant en quelques minutes.",
        "Di lo que quiere el cliente y recibe en minutos un presupuesto claro y convincente.",
    ],
    "nav_quotes": ["Offertes", "Quotes", "Angebote", "Devis", "Presupuestos"],
    "nav_new": ["Nieuwe offerte", "New quote", "Neues Angebot", "Nouveau devis", "Nuevo presupuesto"],
    "nav_products": ["Prijslijst", "Price list", "Preisliste", "Tarifs", "Lista de precios"],
    "nav_settings": ["Instellingen", "Settings", "Einstellungen", "Paramètres", "Ajustes"],
    "logout": ["Uitloggen", "Log out", "Abmelden", "Déconnexion", "Cerrar sesión"],
    "login": ["Inloggen", "Log in", "Anmelden", "Connexion", "Iniciar sesión"],
    "email": ["E-mailadres", "Email address", "E-Mail-Adresse", "Adresse e-mail", "Correo electrónico"],
    "password": ["Wachtwoord", "Password", "Passwort", "Mot de passe", "Contraseña"],
    "no_account": ["Nog geen account?", "No account yet?", "Noch kein Konto?", "Pas encore de compte ?", "¿Aún no tienes cuenta?"],
    "start_trial": ["Start 14 dagen gratis", "Start 14 days free", "14 Tage kostenlos testen", "Essai gratuit 14 jours", "Prueba 14 días gratis"],
    "try_demo": ["Bekijk de demo", "Try the demo", "Demo ansehen", "Voir la démo", "Ver la demo"],
    "have_account": ["Al een account?", "Already have an account?", "Schon ein Konto?", "Déjà un compte ?", "¿Ya tienes cuenta?"],
    "company_name": ["Bedrijfsnaam", "Company name", "Firmenname", "Nom de l'entreprise", "Nombre de la empresa"],
    "country": ["Land", "Country", "Land", "Pays", "País"],
    "language": ["Taal", "Language", "Sprache", "Langue", "Idioma"],
    "wrong_login": ["E-mail of wachtwoord klopt niet.", "Email or password is incorrect.", "E-Mail oder Passwort ist falsch.", "E-mail ou mot de passe incorrect.", "Correo o contraseña incorrectos."],
    "email_taken": ["Dit e-mailadres heeft al een account.", "This email already has an account.", "Für diese E-Mail gibt es schon ein Konto.", "Cet e-mail a déjà un compte.", "Este correo ya tiene una cuenta."],
    "pw_short": ["Kies een wachtwoord van minstens 8 tekens.", "Choose a password of at least 8 characters.", "Wählen Sie ein Passwort mit mindestens 8 Zeichen.", "Choisissez un mot de passe d'au moins 8 caractères.", "Elige una contraseña de al menos 8 caracteres."],
    # dashboard
    "open_quotes": ["Open offertes", "Open quotes", "Offene Angebote", "Devis ouverts", "Presupuestos abiertos"],
    "accepted_month": ["Akkoord deze maand", "Accepted this month", "Angenommen diesen Monat", "Acceptés ce mois", "Aceptados este mes"],
    "hit_rate": ["Scoringskans", "Win rate", "Erfolgsquote", "Taux de réussite", "Tasa de éxito"],
    "open_value": ["Waarde open", "Open value", "Offener Wert", "Valeur ouverte", "Valor abierto"],
    "no_quotes": ["Nog geen offertes. Maak je eerste!", "No quotes yet. Make your first one!", "Noch keine Angebote. Erstellen Sie das erste!", "Pas encore de devis. Créez le premier !", "Aún no hay presupuestos. ¡Haz el primero!"],
    "number": ["Nummer", "Number", "Nummer", "Numéro", "Número"],
    "customer": ["Klant", "Customer", "Kunde", "Client", "Cliente"],
    "date": ["Datum", "Date", "Datum", "Date", "Fecha"],
    "amount": ["Bedrag", "Amount", "Betrag", "Montant", "Importe"],
    "status": ["Status", "Status", "Status", "Statut", "Estado"],
    "st_concept": ["Concept", "Draft", "Entwurf", "Brouillon", "Borrador"],
    "st_verstuurd": ["Verstuurd", "Sent", "Gesendet", "Envoyé", "Enviado"],
    "st_akkoord": ["Akkoord", "Accepted", "Angenommen", "Accepté", "Aceptado"],
    "st_afgewezen": ["Afgewezen", "Declined", "Abgelehnt", "Refusé", "Rechazado"],
    # new quote
    "what_wants": ["Wat wil de klant?", "What does the customer want?", "Was möchte der Kunde?", "Que veut le client ?", "¿Qué quiere el cliente?"],
    "what_wants_help": [
        "Plak de mail of het WhatsApp-bericht van de klant, of spreek het in. Naam en e-mail van de klant mogen er gewoon bij.",
        "Paste the customer's email or message, or dictate it. The customer's name and email can go in too.",
        "Fügen Sie die E-Mail oder Nachricht des Kunden ein oder diktieren Sie sie. Name und E-Mail des Kunden dürfen dabei sein.",
        "Collez l'e-mail ou le message du client, ou dictez-le. Le nom et l'e-mail du client peuvent y figurer.",
        "Pega el correo o mensaje del cliente, o díctalo. El nombre y correo del cliente pueden ir incluidos.",
    ],
    "placeholder_wish": [
        "Bijv.: Hoi, ik ben Sanne van Bakkerij De Korrel (sanne@dekorrel.nl). We willen 40 zwarte T-shirts met ons logo op de rug, vóór 15 december.",
        "E.g.: Hi, I'm Sam from Corner Bakery (sam@cornerbakery.com). We'd like 40 black T-shirts with our logo on the back, before 15 December.",
        "Z. B.: Hallo, ich bin Lena von Bäckerei Korn (lena@korn.de). Wir möchten 40 schwarze T-Shirts mit Logo auf dem Rücken, vor dem 15. Dezember.",
        "Ex. : Bonjour, je suis Claire de la Boulangerie du Coin (claire@ducoin.fr). Nous voudrions 40 T-shirts noirs avec notre logo au dos, avant le 15 décembre.",
        "Ej.: Hola, soy Lucía de Panadería El Grano (lucia@elgrano.es). Queremos 40 camisetas negras con nuestro logo en la espalda, antes del 15 de diciembre.",
    ],
    "quote_language": ["Taal van de offerte", "Quote language", "Sprache des Angebots", "Langue du devis", "Idioma del presupuesto"],
    "make_quote": ["Maak de offerte", "Create the quote", "Angebot erstellen", "Créer le devis", "Crear el presupuesto"],
    "dictate": ["Inspreken", "Dictate", "Diktieren", "Dicter", "Dictar"],
    "listening": ["Ik luister… tik nogmaals om te stoppen", "Listening… tap again to stop", "Ich höre zu… nochmal tippen zum Stoppen", "J'écoute… touchez à nouveau pour arrêter", "Escuchando… toca de nuevo para parar"],
    "sound": ["Geluid", "Sound", "Ton", "Son", "Sonido"],
    "working": ["Nocturo rekent je offerte uit…", "Nocturo is working out your quote…", "Nocturo berechnet Ihr Angebot…", "Nocturo calcule votre devis…", "Nocturo está calculando tu presupuesto…"],
    "empty_pricelist_hint": [
        "Tip: zet eerst je producten en prijzen in de prijslijst, dan rekent Nocturo met jouw prijzen.",
        "Tip: add your products and prices to the price list first, so Nocturo uses your prices.",
        "Tipp: Tragen Sie zuerst Ihre Produkte und Preise in die Preisliste ein, dann rechnet Nocturo mit Ihren Preisen.",
        "Astuce : ajoutez d'abord vos produits et prix dans les tarifs, Nocturo utilisera vos prix.",
        "Consejo: añade primero tus productos y precios a la lista, así Nocturo usará tus precios.",
    ],
    "ai_error": [
        "Het maken lukte even niet. Probeer het nog een keer.",
        "Creating the quote didn't work. Please try again.",
        "Das Erstellen hat nicht geklappt. Bitte noch einmal versuchen.",
        "La création n'a pas fonctionné. Réessayez.",
        "No se pudo crear. Inténtalo de nuevo.",
    ],
    # edit
    "check_points": ["Even nakijken", "Please check", "Bitte prüfen", "À vérifier", "Revisa esto"],
    "customer_name": ["Naam klant", "Customer name", "Name des Kunden", "Nom du client", "Nombre del cliente"],
    "customer_company": ["Bedrijf klant", "Customer company", "Firma des Kunden", "Société du client", "Empresa del cliente"],
    "customer_email": ["E-mail klant", "Customer email", "E-Mail des Kunden", "E-mail du client", "Correo del cliente"],
    "customer_address": ["Adres klant", "Customer address", "Adresse des Kunden", "Adresse du client", "Dirección del cliente"],
    "subject": ["Onderwerp", "Subject", "Betreff", "Objet", "Asunto"],
    "intro": ["Inleiding", "Introduction", "Einleitung", "Introduction", "Introducción"],
    "closing": ["Afsluiting", "Closing", "Abschluss", "Conclusion", "Cierre"],
    "lines": ["Regels", "Lines", "Positionen", "Lignes", "Líneas"],
    "add_line": ["+ Regel toevoegen", "+ Add line", "+ Position hinzufügen", "+ Ajouter une ligne", "+ Añadir línea"],
    "valid_until": ["Geldig tot", "Valid until", "Gültig bis", "Valable jusqu'au", "Válido hasta"],
    "save": ["Opslaan", "Save", "Speichern", "Enregistrer", "Guardar"],
    "saved": ["Opgeslagen", "Saved", "Gespeichert", "Enregistré", "Guardado"],
    "download_pdf": ["PDF downloaden", "Download PDF", "PDF herunterladen", "Télécharger le PDF", "Descargar PDF"],
    "send": ["Versturen", "Send", "Senden", "Envoyer", "Enviar"],
    "customer_link": ["Link voor de klant", "Customer link", "Link für den Kunden", "Lien pour le client", "Enlace para el cliente"],
    "customer_link_help": [
        "Via deze link kan de klant de offerte online bekijken en meteen akkoord geven.",
        "With this link the customer can view the quote online and accept it right away.",
        "Über diesen Link kann der Kunde das Angebot online ansehen und direkt annehmen.",
        "Avec ce lien, le client peut consulter le devis en ligne et l'accepter tout de suite.",
        "Con este enlace el cliente puede ver el presupuesto en línea y aceptarlo al momento.",
    ],
    "copy": ["Kopiëren", "Copy", "Kopieren", "Copier", "Copiar"],
    "copied": ["Gekopieerd", "Copied", "Kopiert", "Copié", "Copiado"],
    "delete": ["Verwijderen", "Delete", "Löschen", "Supprimer", "Eliminar"],
    "confirm_delete": ["Weet je het zeker?", "Are you sure?", "Sind Sie sicher?", "Êtes-vous sûr ?", "¿Seguro?"],
    "duplicate": ["Kopie maken", "Duplicate", "Duplizieren", "Dupliquer", "Duplicar"],
    "set_status": ["Status wijzigen", "Change status", "Status ändern", "Changer le statut", "Cambiar estado"],
    "description": ["Omschrijving", "Description", "Beschreibung", "Description", "Descripción"],
    "qty": ["Aantal", "Qty", "Menge", "Qté", "Cant."],
    "unit": ["Eenheid", "Unit", "Einheit", "Unité", "Unidad"],
    "price": ["Prijs", "Price", "Preis", "Prix", "Precio"],
    "vat": ["Btw", "VAT", "MwSt.", "TVA", "IVA"],
    "price_excl": ["Prijs excl. btw", "Price excl. VAT", "Preis netto", "Prix HT", "Precio sin IVA"],
    "subtotal": ["Subtotaal", "Subtotal", "Zwischensumme", "Sous-total", "Subtotal"],
    "total": ["Totaal", "Total", "Gesamt", "Total", "Total"],
    "missing_price": ["Prijs ontbreekt", "Price missing", "Preis fehlt", "Prix manquant", "Falta el precio"],
    "back": ["Terug", "Back", "Zurück", "Retour", "Volver"],
    # send
    "send_title": ["Offerte versturen", "Send quote", "Angebot senden", "Envoyer le devis", "Enviar presupuesto"],
    "to": ["Aan", "To", "An", "À", "Para"],
    "message": ["Bericht", "Message", "Nachricht", "Message", "Mensaje"],
    "send_now": ["Nu versturen", "Send now", "Jetzt senden", "Envoyer maintenant", "Enviar ahora"],
    "sent_ok": ["De offerte is verstuurd.", "The quote has been sent.", "Das Angebot wurde gesendet.", "Le devis a été envoyé.", "El presupuesto ha sido enviado."],
    "send_failed": ["Versturen lukte niet:", "Sending failed:", "Senden fehlgeschlagen:", "L'envoi a échoué :", "Error al enviar:"],
    "mail_not_set": [
        "Versturen per mail staat nog niet aan. Download de PDF of stuur de klantlink zelf door.",
        "Email sending is not switched on yet. Download the PDF or share the customer link yourself.",
        "Der E-Mail-Versand ist noch nicht aktiv. Laden Sie das PDF herunter oder teilen Sie den Kundenlink selbst.",
        "L'envoi par e-mail n'est pas encore activé. Téléchargez le PDF ou partagez vous-même le lien client.",
        "El envío por correo aún no está activo. Descarga el PDF o comparte tú el enlace del cliente.",
    ],
    "demo_no_send": [
        "In de demo wordt er niets echt verstuurd. Start een gratis proef om echt te versturen.",
        "Nothing is really sent in the demo. Start a free trial to send for real.",
        "In der Demo wird nichts wirklich gesendet. Starten Sie eine kostenlose Testphase, um echt zu senden.",
        "Rien n'est réellement envoyé dans la démo. Lancez un essai gratuit pour envoyer pour de vrai.",
        "En la demo no se envía nada de verdad. Empieza una prueba gratis para enviar de verdad.",
    ],
    "attach_note": ["De PDF gaat als bijlage mee, plus de link om online akkoord te geven.", "The PDF is attached, plus the link to accept online.", "Das PDF wird angehängt, dazu der Link zur Online-Annahme.", "Le PDF est joint, avec le lien pour accepter en ligne.", "Se adjunta el PDF y el enlace para aceptar en línea."],
    # products
    "products_intro": [
        "Je producten en diensten met prijzen. Nocturo gebruikt deze lijst om offertes uit te rekenen.",
        "Your products and services with prices. Nocturo uses this list to work out quotes.",
        "Ihre Produkte und Leistungen mit Preisen. Nocturo berechnet damit die Angebote.",
        "Vos produits et services avec leurs prix. Nocturo s'en sert pour calculer les devis.",
        "Tus productos y servicios con precios. Nocturo usa esta lista para calcular los presupuestos.",
    ],
    "product": ["Product of dienst", "Product or service", "Produkt oder Leistung", "Produit ou service", "Producto o servicio"],
    "add": ["Toevoegen", "Add", "Hinzufügen", "Ajouter", "Añadir"],
    "import_title": ["Prijslijst inplakken", "Paste a price list", "Preisliste einfügen", "Coller une liste de prix", "Pegar lista de precios"],
    "import_help": [
        "Heb je al een prijslijst (van je website, Excel of een folder)? Plak hem hier en Nocturo zet hem netjes in je lijst.",
        "Already have a price list (website, Excel, brochure)? Paste it here and Nocturo puts it neatly into your list.",
        "Schon eine Preisliste (Website, Excel, Prospekt)? Hier einfügen, Nocturo übernimmt sie ordentlich.",
        "Vous avez déjà une liste de prix (site, Excel, brochure) ? Collez-la ici et Nocturo la range proprement.",
        "¿Ya tienes una lista de precios (web, Excel, folleto)? Pégala aquí y Nocturo la ordena en tu lista.",
    ],
    "import_btn": ["Inlezen", "Import", "Einlesen", "Importer", "Importar"],
    "imported": ["regels toegevoegd aan je prijslijst.", "lines added to your price list.", "Positionen zur Preisliste hinzugefügt.", "lignes ajoutées à vos tarifs.", "líneas añadidas a tu lista."],
    "no_products": ["Je prijslijst is nog leeg.", "Your price list is still empty.", "Ihre Preisliste ist noch leer.", "Vos tarifs sont encore vides.", "Tu lista de precios aún está vacía."],
    # settings
    "company_details": ["Bedrijfsgegevens", "Company details", "Firmendaten", "Coordonnées", "Datos de la empresa"],
    "address": ["Adres", "Address", "Adresse", "Adresse", "Dirección"],
    "postcode_city": ["Postcode en plaats", "Postcode and city", "PLZ und Ort", "Code postal et ville", "Código postal y ciudad"],
    "phone": ["Telefoon", "Phone", "Telefon", "Téléphone", "Teléfono"],
    "website": ["Website", "Website", "Website", "Site web", "Sitio web"],
    "coc": ["KvK-nummer", "Company reg. no.", "Handelsregister-Nr.", "SIREN/SIRET", "CIF/NIF"],
    "vat_no": ["Btw-nummer", "VAT number", "USt-IdNr.", "N° TVA", "N.º IVA"],
    "iban": ["IBAN", "IBAN", "IBAN", "IBAN", "IBAN"],
    "logo": ["Logo", "Logo", "Logo", "Logo", "Logo"],
    "logo_help": ["PNG of JPG, max. 1 MB.", "PNG or JPG, max. 1 MB.", "PNG oder JPG, max. 1 MB.", "PNG ou JPG, 1 Mo max.", "PNG o JPG, máx. 1 MB."],
    "accent": ["Kleur op de offerte", "Colour on the quote", "Farbe im Angebot", "Couleur du devis", "Color del presupuesto"],
    "quote_settings": ["Offerte-instellingen", "Quote settings", "Angebotseinstellungen", "Paramètres des devis", "Ajustes del presupuesto"],
    "default_vat": ["Standaard btw %", "Default VAT %", "Standard-MwSt. %", "TVA par défaut %", "IVA por defecto %"],
    "validity_days": ["Geldig (dagen)", "Valid (days)", "Gültig (Tage)", "Validité (jours)", "Validez (días)"],
    "prefix": ["Voorvoegsel nummer", "Number prefix", "Nummernpräfix", "Préfixe du numéro", "Prefijo del número"],
    "terms": ["Voorwaarden onderaan", "Terms at the bottom", "Bedingungen unten", "Conditions en bas", "Condiciones al pie"],
    "terms_ph": [
        "Bijv.: Betaling binnen 14 dagen na levering. Prijzen zijn exclusief verzendkosten.",
        "E.g.: Payment within 14 days of delivery. Prices exclude shipping.",
        "Z. B.: Zahlung innerhalb von 14 Tagen nach Lieferung. Preise zzgl. Versand.",
        "Ex. : Paiement sous 14 jours après livraison. Frais de port non compris.",
        "Ej.: Pago en 14 días tras la entrega. Precios sin gastos de envío.",
    ],
    "trial_left": ["Gratis proef: nog {n} dagen", "Free trial: {n} days left", "Kostenlose Testphase: noch {n} Tage", "Essai gratuit : encore {n} jours", "Prueba gratis: quedan {n} días"],
    "trial_over": [
        "Je gratis proef is voorbij. Neem contact op via info@nocturoapps.com om door te gaan.",
        "Your free trial has ended. Contact info@nocturoapps.com to continue.",
        "Ihre Testphase ist abgelaufen. Kontakt: info@nocturoapps.com, um weiterzumachen.",
        "Votre essai gratuit est terminé. Contactez info@nocturoapps.com pour continuer.",
        "Tu prueba gratis ha terminado. Escribe a info@nocturoapps.com para continuar.",
    ],
    "demo_banner": [
        "Dit is de demo. Kijk gerust rond, alles mag. Wil je het voor je eigen bedrijf?",
        "This is the demo. Look around freely. Want it for your own business?",
        "Dies ist die Demo. Schauen Sie sich frei um. Für Ihr eigenes Unternehmen?",
        "Ceci est la démo. Explorez librement. Vous le voulez pour votre entreprise ?",
        "Esta es la demo. Explora libremente. ¿Lo quieres para tu empresa?",
    ],
    # public
    "accept": ["Akkoord geven", "Accept quote", "Angebot annehmen", "Accepter le devis", "Aceptar presupuesto"],
    "decline": ["Liever niet", "Decline", "Ablehnen", "Refuser", "Rechazar"],
    "your_name": ["Je naam", "Your name", "Ihr Name", "Votre nom", "Tu nombre"],
    "thanks_accept": ["Dank je wel! Je akkoord is doorgegeven.", "Thank you! Your acceptance has been sent.", "Vielen Dank! Ihre Zusage wurde übermittelt.", "Merci ! Votre accord a été transmis.", "¡Gracias! Tu aceptación se ha enviado."],
    "thanks_decline": ["Bedankt voor je reactie.", "Thanks for letting us know.", "Danke für Ihre Rückmeldung.", "Merci pour votre réponse.", "Gracias por tu respuesta."],
    "accepted_by": ["Akkoord gegeven door", "Accepted by", "Angenommen von", "Accepté par", "Aceptado por"],
    "admin": ["Beheer", "Admin", "Verwaltung", "Administration", "Administración"],
}

_DOC = {
    "quote": ["OFFERTE", "QUOTE", "ANGEBOT", "DEVIS", "PRESUPUESTO"],
    "number": ["Offertenummer", "Quote number", "Angebotsnummer", "Numéro de devis", "Número de presupuesto"],
    "date": ["Datum", "Date", "Datum", "Date", "Fecha"],
    "valid_until": ["Geldig tot", "Valid until", "Gültig bis", "Valable jusqu'au", "Válido hasta"],
    "for": ["Voor", "For", "Für", "Pour", "Para"],
    "description": ["Omschrijving", "Description", "Beschreibung", "Description", "Descripción"],
    "qty": ["Aantal", "Qty", "Menge", "Qté", "Cant."],
    "price": ["Prijs", "Price", "Einzelpreis", "Prix unit.", "Precio"],
    "vat": ["Btw", "VAT", "MwSt.", "TVA", "IVA"],
    "amount": ["Bedrag", "Amount", "Betrag", "Montant", "Importe"],
    "subtotal": ["Subtotaal", "Subtotal", "Zwischensumme", "Sous-total HT", "Subtotal"],
    "vat_line": ["Btw {p}%", "VAT {p}%", "MwSt. {p} %", "TVA {p} %", "IVA {p}%"],
    "total": ["Totaal", "Total", "Gesamtbetrag", "Total TTC", "Total"],
    "excl": ["Bedragen in euro.", "Amounts in euros.", "Beträge in Euro.", "Montants en euros.", "Importes en euros."],
    "accept_online": ["Akkoord? Geef het online door via:", "Agree? Accept online at:", "Einverstanden? Online annehmen unter:", "D'accord ? Acceptez en ligne :", "¿De acuerdo? Acepta en línea en:"],
    "coc": ["KvK", "Reg. no.", "HRB", "SIRET", "CIF"],
    "vat_no": ["Btw-nr.", "VAT no.", "USt-IdNr.", "N° TVA", "N.º IVA"],
    "iban": ["IBAN", "IBAN", "IBAN", "IBAN", "IBAN"],
    "accepted": ["Akkoord gegeven op {d} door {n}", "Accepted on {d} by {n}", "Angenommen am {d} von {n}", "Accepté le {d} par {n}", "Aceptado el {d} por {n}"],
    "mail_subject": ["Offerte {n} van {c}", "Quote {n} from {c}", "Angebot {n} von {c}", "Devis {n} de {c}", "Presupuesto {n} de {c}"],
    "mail_body": [
        "Beste {k},\n\nHierbij ontvang je onze offerte {n}. Je vindt hem als PDF in de bijlage.\n\nAkkoord? Dat kun je meteen online doorgeven via deze link:\n{l}\n\nHeb je nog vragen, dan hoor ik het graag.\n\nMet vriendelijke groet,\n{c}",
        "Dear {k},\n\nPlease find attached our quote {n} as a PDF.\n\nHappy with it? You can accept it online right away via this link:\n{l}\n\nIf you have any questions, just let me know.\n\nKind regards,\n{c}",
        "Guten Tag {k},\n\nanbei erhalten Sie unser Angebot {n} als PDF.\n\nEinverstanden? Sie können es direkt online annehmen:\n{l}\n\nBei Fragen melden Sie sich gern.\n\nMit freundlichen Grüßen\n{c}",
        "Bonjour {k},\n\nVeuillez trouver ci-joint notre devis {n} en PDF.\n\nVous êtes d'accord ? Vous pouvez l'accepter en ligne via ce lien :\n{l}\n\nPour toute question, n'hésitez pas.\n\nCordialement,\n{c}",
        "Hola {k}:\n\nTe adjuntamos nuestro presupuesto {n} en PDF.\n\n¿Te parece bien? Puedes aceptarlo en línea con este enlace:\n{l}\n\nSi tienes alguna pregunta, dímelo.\n\nUn saludo,\n{c}",
    ],
    "made_with": ["Gemaakt met Nocturo Offerte", "Made with Nocturo Quote", "Erstellt mit Nocturo Angebot", "Réalisé avec Nocturo Devis", "Hecho con Nocturo Presupuesto"],
}


STEPS = {
    "nl": ["De wens van de klant lezen", "Naam en e-mail van de klant opzoeken", "In je prijslijst snuffelen",
           "De juiste staffelprijs zoeken", "Vaste kosten erbij: opstartkosten, verzending", "Btw uitrekenen",
           "Een persoonlijke inleiding schrijven", "Nog één keer alles nalopen"],
    "en": ["Reading the customer's request", "Finding the customer's name and email", "Digging through your price list",
           "Picking the right volume price", "Adding fixed costs: setup, shipping", "Working out the VAT",
           "Writing a personal introduction", "Double-checking everything"],
    "de": ["Den Kundenwunsch lesen", "Name und E-Mail des Kunden heraussuchen", "In Ihrer Preisliste stöbern",
           "Den passenden Staffelpreis suchen", "Fixkosten dazu: Einrichtung, Versand", "Mehrwertsteuer berechnen",
           "Eine persönliche Einleitung schreiben", "Alles noch einmal prüfen"],
    "fr": ["Lecture de la demande du client", "Recherche du nom et de l'e-mail du client", "Exploration de vos tarifs",
           "Choix du bon prix dégressif", "Ajout des frais fixes : mise en route, livraison", "Calcul de la TVA",
           "Rédaction d'une introduction personnelle", "Dernière vérification"],
    "es": ["Leyendo la petición del cliente", "Buscando el nombre y correo del cliente", "Revisando tu lista de precios",
           "Eligiendo el precio por volumen correcto", "Añadiendo costes fijos: preparación, envío", "Calculando el IVA",
           "Escribiendo una introducción personal", "Revisándolo todo una última vez"],
}


def _idx(lang: str) -> int:
    return LANGS.index(lang) if lang in LANGS else 0


def t(key: str, lang: str = "nl", **kw) -> str:
    vals = _UI.get(key)
    if vals is None:
        return key
    s = vals[_idx(lang)]
    return s.format(**kw) if kw else s


def d(key: str, lang: str = "nl", **kw) -> str:
    vals = _DOC.get(key)
    if vals is None:
        return key
    s = vals[_idx(lang)]
    return s.format(**kw) if kw else s


def money(value, lang: str = "nl") -> str:
    """Bedrag netjes per taal: € 1.234,56 (nl/de/es), 1 234,56 € (fr), €1,234.56 (en)."""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        v = 0.0
    neg = v < 0
    s = f"{abs(v):,.2f}"  # 1,234.56
    if lang == "en":
        out = f"€{s}"
    elif lang == "fr":
        out = s.replace(",", " ").replace(".", ",") + " €"
    else:
        out = "€ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if neg else "") + out


def number(value, lang: str = "nl") -> str:
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return str(value)
    s = f"{v:g}" if v == int(v) else f"{v:.2f}".rstrip("0")
    return s if lang == "en" else s.replace(".", ",")


def date_str(dt, lang: str = "nl") -> str:
    if not dt:
        return ""
    if lang == "en":
        return dt.strftime("%d %b %Y")
    return dt.strftime("%d-%m-%Y") if lang == "nl" else dt.strftime("%d.%m.%Y") if lang == "de" else dt.strftime("%d/%m/%Y")
