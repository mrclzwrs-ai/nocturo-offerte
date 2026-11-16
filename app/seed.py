"""Demo-account: een verzonnen textieldrukkerij, zodat bezoekers meteen kunnen proberen."""
import json
from datetime import datetime, timedelta

from .models import Company, Product, Quote

DEMO_EMAIL = "demo@nocturoapps.com"

DEMO_PRODUCTS = [
    ("T-shirt basic katoen", "Unisex, 180 g/m², kleuren: wit, zwart, navy, grijs", "stuk", 4.95),
    ("T-shirt premium biokatoen", "Unisex, 220 g/m², fairtrade", "stuk", 8.50),
    ("Hoodie", "Met capuchon en buidelzak, 300 g/m²", "stuk", 17.95),
    ("Katoenen tas", "Naturel, 38 × 42 cm, lange hengsels", "stuk", 2.40),
    ("Zeefdruk 1 kleur, 10-49 st.", "Per bedrukking per kledingstuk", "stuk", 3.20),
    ("Zeefdruk 1 kleur, 50-249 st.", "Per bedrukking per kledingstuk", "stuk", 2.10),
    ("Zeefdruk extra kleur", "Per extra kleur per kledingstuk", "stuk", 0.90),
    ("Zeefkosten", "Eenmalig per kleur per ontwerp", "zeef", 25.00),
    ("Borduren logo tot 8 cm", "Inclusief digitaliseren vanaf 25 st.", "stuk", 5.75),
    ("Ontwerp aanpassen", "Logo of tekst drukklaar maken", "uur", 45.00),
    ("Verzending NL/BE", "Per zending, track & trace", "zending", 9.95),
]


def ensure_demo(db) -> Company:
    c = db.query(Company).filter(Company.email == DEMO_EMAIL).first()
    if not c:
        c = Company(
            email=DEMO_EMAIL, password_hash="!", name="Studio Inktvis", is_demo=True,
            address="Voorbeeldstraat 12", postcode_city="1234 AB Voorbeeldstad", country="Nederland",
            phone="+31 6 00 00 00 00", website="www.studio-inktvis.example", coc="00000000",
            vat_no="NL000000000B01", iban="NL00 BANK 0000 0000 00", accent="#0F8B78", prefix="SI-",
            terms="Betaling binnen 14 dagen na levering. Levertijd ca. 10 werkdagen na akkoord op de proef.",
            next_number=3, default_vat=21.0, validity_days=30,
        )
        db.add(c)
        db.flush()
        for name, desc, unit, price in DEMO_PRODUCTS:
            db.add(Product(company_id=c.id, name=name, description=desc, unit=unit, price=price, vat=21.0))
        now = datetime.utcnow()
        db.add(Quote(
            company_id=c.id, number=f"SI-{now.year}-001", status="akkoord", lang="nl",
            customer_name="Sanne de Vries", customer_company="Bakkerij De Korrel", customer_email="sanne@example.com",
            title="40 T-shirts met logo op de rug",
            intro="Leuk dat je aan ons denkt voor de nieuwe shirts van de bakkerij! Hieronder vind je de offerte voor 40 zwarte T-shirts met jullie logo op de rug.",
            closing="Bij akkoord vóór 1 december heb je de shirts ruim op tijd binnen. We sturen eerst een digitale proef ter goedkeuring.",
            lines_json=json.dumps([
                {"description": "T-shirt basic katoen, zwart", "qty": 40, "unit": "stuk", "price": 4.95, "vat": 21},
                {"description": "Zeefdruk 1 kleur rug (10-49 st.)", "qty": 40, "unit": "stuk", "price": 3.20, "vat": 21},
                {"description": "Zeefkosten", "qty": 1, "unit": "zeef", "price": 25.00, "vat": 21},
                {"description": "Verzending NL/BE", "qty": 1, "unit": "zending", "price": 9.95, "vat": 21},
            ]),
            date=now - timedelta(days=6), valid_until=now + timedelta(days=24),
            decided_at=now - timedelta(days=2), decided_by="Sanne de Vries", sent_at=now - timedelta(days=6),
        ))
        db.add(Quote(
            company_id=c.id, number=f"SI-{now.year}-002", status="verstuurd", lang="en",
            customer_name="Tom Becker", customer_company="Harbour Sailing Club", customer_email="tom@example.com",
            title="Club hoodies with embroidered logo",
            intro="Thanks for your request! Here is our quote for 25 hoodies with your club logo embroidered on the chest.",
            closing="Delivery about 10 working days after you approve the proof.",
            lines_json=json.dumps([
                {"description": "Hoodie, navy", "qty": 25, "unit": "pcs", "price": 17.95, "vat": 21},
                {"description": "Embroidered logo up to 8 cm (chest)", "qty": 25, "unit": "pcs", "price": 5.75, "vat": 21},
                {"description": "Shipping NL/BE", "qty": 1, "unit": "shipment", "price": 9.95, "vat": 21},
            ]),
            date=now - timedelta(days=1), valid_until=now + timedelta(days=29), sent_at=now - timedelta(days=1),
        ))
        db.commit()
    else:
        # demo netjes houden: maximaal 25 offertes, oudste extra's eruit
        quotes = db.query(Quote).filter(Quote.company_id == c.id).order_by(Quote.created_at.desc()).all()
        extra = [q for q in quotes if not q.number.endswith(("-001", "-002"))]
        for q in extra[20:]:
            db.delete(q)
        db.commit()
    return c
