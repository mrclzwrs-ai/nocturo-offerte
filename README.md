# Nocturo Offerte

Van wat de klant wil naar een nette offerte. Onderdeel van Nocturo (nocturoapps.com).

## Wat zit erin
- Eigen account per bedrijf (14 dagen gratis proef), plus een demo-account (`/demo`)
- Bedrijfsgegevens, logo en kleur op de offerte
- Prijslijst, ook in te plakken (AI zet hem netjes in de lijst)
- Wens van de klant plakken of inspreken: Claude maakt de offerte met de eigen prijzen
- Offertes in 5 talen (NL, EN, DE, FR, ES), scherm ook in 5 talen
- PDF, versturen per mail, klantlink waarmee de klant online akkoord geeft
- Overzicht met status en cijfers; beheerpagina `/beheer` voor de eigenaar

## Draaien op Render (Docker)
Omgevingsvariabelen:

| Naam | Waarde |
|---|---|
| `DATABASE_URL` | Postgres-adres van Render |
| `SECRET_KEY` | lange willekeurige tekst |
| `ANTHROPIC_API_KEY` | Claude-sleutel |
| `ADMIN_EMAIL` | e-mailadres van het beheerdersaccount |
| `BASE_URL` | bijv. `https://offerte.nocturoapps.com` |
| `DB_SCHEMA` | `offerte` (eigen vakje in een gedeelde database) |
| `HTTPS_ONLY` | `1` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | voor het mailen (optioneel) |

Lokaal testen zonder sleutel: `FAKE_AI=1 uvicorn app.main:app --reload`
