import os
import secrets
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./nocturo_offerte.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
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
        if self.is_demo:
            return True
        now = datetime.utcnow()
        if self.paid_until and self.paid_until > now:
            return True
        return bool(self.trial_ends and self.trial_ends > now)

    def trial_days_left(self):
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


def init_db():
    Base.metadata.create_all(engine)
