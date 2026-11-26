import os
import secrets
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./nocturo_offerte.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if DATABASE_URL.startswith("postgresql://"):
    # SQLAlchemy 2.1 kiest anders psycopg 3; wij gebruiken psycopg2
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
# Eigen vakje (schema) binnen een gedeelde Postgres-database, zodat Offerte
# niet in de weg zit van andere apps die dezelfde database gebruiken.
DB_SCHEMA = os.environ.get("DB_SCHEMA", "").strip()
if DB_SCHEMA and not DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import event, text

    @event.listens_for(engine, "connect")
    def _set_search_path(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"')
        cur.execute(f'SET search_path TO "{DB_SCHEMA}"')
        cur.close()
        dbapi_conn.commit()

SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

TRIAL_DAYS = 14


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(255), default="")
    postcode_city = Column(String(255), default="")
    country = Column(String(100), default="")
    phone = Column(String(100), default="")
    website = Column(String(255), default="")
    coc = Column(String(100), default="")
    vat_no = Column(String(100), default="")
    iban = Column(String(100), default="")
    logo_data = Column(Text, default="")  # data:image/...;base64,...
    accent = Column(String(20), default="#0F8B78")
    lang = Column(String(5), default="nl")
    default_vat = Column(Float, default=21.0)
    validity_days = Column(Integer, default=30)
    prefix = Column(String(20), default="OFF-")
    next_number = Column(Integer, default=1)
    terms = Column(Text, default="")
    doelgroep = Column(String(10), default="")   # b2b / b2c, gekozen bij de eerste keer inloggen
    is_demo = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)   # Marcel kan een account aan/uit zetten
    paid_until = Column(DateTime, nullable=True)  # gezet zodra er betaald wordt
    trial_ends = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=TRIAL_DAYS))
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="company", cascade="all, delete-orphan")

    def access_ok(self) -> bool:
        if not self.is_active:
            return False
        if self.is_demo or getattr(self, "_extra_toegang", False):
            return True
        now = datetime.utcnow()
        if self.paid_until and self.paid_until > now:
            return True
        return bool(self.trial_ends and self.trial_ends > now)

    def trial_days_left(self):
        if getattr(self, "_extra_toegang", False):
            return None
        if self.is_demo or (self.paid_until and self.paid_until > datetime.utcnow()):
            return None
        if not self.trial_ends:
            return 0
        return max(0, (self.trial_ends - datetime.utcnow()).days + 1)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    unit = Column(String(50), default="")
    price = Column(Float, default=0.0)  # excl. btw
    vat = Column(Float, default=21.0)
    company = relationship("Company", back_populates="products")


class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    number = Column(String(50), nullable=False)
    status = Column(String(20), default="concept")  # concept / verstuurd / akkoord / afgewezen
    lang = Column(String(5), default="nl")
    customer_name = Column(String(255), default="")
    customer_company = Column(String(255), default="")
    customer_email = Column(String(255), default="")
    customer_address = Column(Text, default="")
    title = Column(String(255), default="")
    intro = Column(Text, default="")
    closing = Column(Text, default="")
    lines_json = Column(Text, default="[]")
    notes_json = Column(Text, default="[]")  # punten om na te kijken (van de AI)
    request_text = Column(Text, default="")
    date = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    token = Column(String(64), unique=True, index=True, default=lambda: secrets.token_urlsafe(24))
    sent_at = Column(DateTime, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    company = relationship("Company", back_populates="quotes")


class AppSub(Base):
    """Welke Nocturo-apps een account huurt (behalve Offerte, die heeft eigen proef/betaald)."""
    __tablename__ = "nocturo_apps"
    __table_args__ = (UniqueConstraint("company_id", "app", name="uq_company_app"),)
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    app = Column(String(30), nullable=False)          # search / video / pling / controlroom
    status = Column(String(20), default="aangevraagd")  # aangevraagd / actief / uit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class SAProfiel(Base):
    """Search & Analyze-instellingen van één klant."""
    __tablename__ = "nocturo_sa_profiel"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, unique=True, index=True)
    aanbod = Column(Text, default="")          # wat je verkoopt en waarom het past bij webwinkels
    link = Column(String(255), default="")      # jouw website
    afzender = Column(String(255), default="")  # naam onder de mail
    smtp_user = Column(String(255), default="")
    smtp_pass = Column(Text, default="")        # versleuteld
    smtp_server = Column(String(255), default="smtp.gmail.com")
    smtp_port = Column(Integer, default=465)
    landen = Column(String(100), default="NL,BE")
    niche = Column(String(255), default="")
    per_dag = Column(Integer, default=10)
    aan = Column(Boolean, default=False)        # dagelijkse ronde aan/uit
    laatste_ronde = Column(DateTime, nullable=True)
    melding = Column(Text, default="")          # laatste fout of opmerking


class SALead(Base):
    """Eén winkel die Search & Analyze voor een klant heeft gevonden en gemaild."""
    __tablename__ = "nocturo_sa_lead"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    domein = Column(String(255), default="", index=True)
    email = Column(String(255), default="")
    winkelnaam = Column(String(255), default="")
    website = Column(String(255), default="")
    land = Column(String(10), default="")
    onderwerp = Column(String(255), default="")
    tekst = Column(Text, default="")
    rapport = Column(Text, default="")
    status = Column(String(30), default="verstuurd")  # verstuurd / mislukt
    fout = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Media(Base):
    """Foto's die klanten uploaden (voor Video Ads); openbaar op /media/<token>."""
    __tablename__ = "nocturo_media"
    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, index=True, default=lambda: secrets.token_urlsafe(24))
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    mime = Column(String(50), default="image/jpeg")
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Video(Base):
    """Eén Video Ads-filmpje."""
    __tablename__ = "nocturo_video"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    title = Column(String(255), default="")
    price = Column(Float, default=0.0)
    description = Column(Text, default="")
    lang = Column(String(5), default="nl")
    stijl = Column(String(20), default="foto")    # foto / luxe / licht
    muziek = Column(String(60), default="")       # leeg = het kantoor kiest
    winkel = Column(String(255), default="")      # naam van de winkel in het filmpje
    site = Column(String(255), default="")        # website in het filmpje
    media_tokens = Column(Text, default="")      # komma-gescheiden
    voiceover = Column(Text, default="")
    status = Column(String(20), default="pending")  # pending / processing / completed / failed
    render_id = Column(String(100), default="")
    url = Column(String(500), default="")
    thumb = Column(String(500), default="")
    error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class WebsiteCheck(Base):
    """Eén website-check met verkoopplan (hoort bij Video Ads)."""
    __tablename__ = "nocturo_check"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    url = Column(String(500), default="")
    status = Column(String(20), default="pending")  # pending / processing / done / failed
    result_json = Column(Text, default="")
    error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    # nieuwe kolommen bij bestaande tabellen
    from sqlalchemy import text as _sql
    try:
        with engine.begin() as con:
            if engine.dialect.name == "postgresql":
                con.execute(_sql("ALTER TABLE nocturo_video ADD COLUMN IF NOT EXISTS stijl VARCHAR(20) DEFAULT 'foto'"))
                con.execute(_sql("ALTER TABLE companies ADD COLUMN IF NOT EXISTS doelgroep VARCHAR(10) DEFAULT ''"))
                con.execute(_sql("ALTER TABLE nocturo_video ADD COLUMN IF NOT EXISTS muziek VARCHAR(60) DEFAULT ''"))
                con.execute(_sql("ALTER TABLE nocturo_video ADD COLUMN IF NOT EXISTS winkel VARCHAR(255) DEFAULT ''"))
                con.execute(_sql("ALTER TABLE nocturo_video ADD COLUMN IF NOT EXISTS site VARCHAR(255) DEFAULT ''"))
            else:
                kols = [r[1] for r in con.execute(_sql("PRAGMA table_info(nocturo_video)"))]
                if "stijl" not in kols:
                    con.execute(_sql("ALTER TABLE nocturo_video ADD COLUMN stijl VARCHAR(20) DEFAULT 'foto'"))
                if "muziek" not in kols:
                    con.execute(_sql("ALTER TABLE nocturo_video ADD COLUMN muziek VARCHAR(60) DEFAULT ''"))
                for kol in ("winkel", "site"):
                    if kol not in kols:
                        con.execute(_sql(f"ALTER TABLE nocturo_video ADD COLUMN {kol} VARCHAR(255) DEFAULT ''"))
                kols = [r[1] for r in con.execute(_sql("PRAGMA table_info(companies)"))]
                if "doelgroep" not in kols:
                    con.execute(_sql("ALTER TABLE companies ADD COLUMN doelgroep VARCHAR(10) DEFAULT ''"))
    except Exception as ex:
        print("Kolom stijl toevoegen mislukt:", ex)
