import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from . import ai
from .calc import lines_of, notes_of, totals
from .i18n import LANGS, LANG_NAMES, STEPS, d, date_str, money, number, t
from .mailer import mail_ready, send_quote_mail
from .models import Company, Product, Quote, SessionLocal, init_db
from .seed import DEMO_EMAIL, ensure_demo

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-" + secrets.token_hex(16)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")

app = FastAPI(title="Nocturo Offerte", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax",
                   https_only=os.environ.get("HTTPS_ONLY", "0") == "1", max_age=60 * 60 * 24 * 30)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

STATUSES = ["concept", "verstuurd", "akkoord", "afgewezen"]


@app.on_event("startup")
def _startup():
    init_db()
    with SessionLocal() as db:
        ensure_demo(db)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- wachtwoorden ----------
def hash_pw(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(h).decode()


def check_pw(pw: str, stored: str) -> bool:
    try:
        _, s, h = stored.split("$")
        calc = hashlib.scrypt(pw.encode(), salt=base64.b64decode(s), n=2 ** 14, r=8, p=1)
        return hmac.compare_digest(calc, base64.b64decode(h))
    except Exception:
        return False


# ---------- hulpjes ----------
def ui_lang(request: Request, company=None) -> str:
    if company is not None:
        return company.lang or "nl"
    lang = request.session.get("lang")
    if lang in LANGS:
        return lang
    accept = (request.headers.get("accept-language") or "").lower()
    for code in LANGS:
        if accept.startswith(code):
            return code
    return "nl"


def current_company(request: Request, db) -> Company | None:
    cid = request.session.get("cid")
    if not cid:
        return None
    c = db.get(Company, cid)
    if not c or not c.is_active:
        request.session.clear()
        return None
    return c


def need_company(request: Request, db) -> Company:
    c = current_company(request, db)
    if not c:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return c


def base_url(request: Request) -> str:
    return BASE_URL or str(request.base_url).rstrip("/")


def render(request: Request, name: str, company=None, lang=None, **ctx):
    lang = lang or ui_lang(request, company)
    flash = request.session.pop("flash", None)
    ctx.update(
        request=request, c=company, lang=lang, langs=LANGS, lang_names=LANG_NAMES,
        T=lambda k, **kw: t(k, lang, **kw), MONEY=lambda v: money(v, lang), NUM=lambda v: number(v, lang),
        DATE=lambda v: date_str(v, lang), flash=flash, steps=STEPS.get(lang, STEPS['nl']), is_admin=bool(company and ADMIN_EMAIL and company.email == ADMIN_EMAIL),
    )
    return templates.TemplateResponse(request, name, ctx)


def flash(request: Request, msg: str, kind: str = "ok"):
    request.session["flash"] = {"msg": msg, "kind": kind}


def go(url: str):
    return RedirectResponse(url, status_code=303)


def own_quote(db, company, qid: int) -> Quote:
    q = db.get(Quote, qid)
    if not q or q.company_id != company.id:
        raise HTTPException(404)
    return q


def parse_float(v, default=0.0):
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return default


# eenvoudige rem tegen misbruik van de AI (vooral in de demo)
_ai_hits: dict = {}


def ai_allowed(key: str, limit: int) -> bool:
    now = time.time()
    hits = [h for h in _ai_hits.get(key, []) if now - h < 3600]
    if len(hits) >= limit:
        _ai_hits[key] = hits
        return False
    hits.append(now)
    _ai_hits[key] = hits
    return True


# ---------- PDF ----------
def quote_pdf(request: Request, q: Quote) -> bytes:
    from weasyprint import HTML

    c = q.company
    ql = q.lang or "nl"
    lines = lines_of(q)
    html = templates.get_template("quote_doc.html").render(
        c=c, q=q, ql=ql, lines=lines, tot=totals(lines), accent=c.accent or "#0F8B78",
        public_url=f"{base_url(request)}/q/{q.token}",
        D=lambda k, **kw: d(k, ql, **kw), MONEY=lambda v: money(v, ql), NUM=lambda v: number(v, ql),
        DATE=lambda v: date_str(v, ql),
    )
    return HTML(string=html, base_url=str(BASE_DIR)).write_pdf()


def pdf_name(q: Quote) -> str:
    safe = "".join(ch for ch in q.number if ch.isalnum() or ch in "-_")
    return f"{d('quote', q.lang).capitalize()}-{safe}.pdf"


# ---------- algemeen ----------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def home(request: Request, db=Depends(get_db)):
    return go("/offertes" if current_company(request, db) else "/login")


@app.get("/taal/{code}")
def set_lang(code: str, request: Request, db=Depends(get_db)):
    if code in LANGS:
        request.session["lang"] = code
        c = current_company(request, db)
        if c and not c.is_demo:
            c.lang = code
            db.commit()
        elif c and c.is_demo:
            request.session["demo_lang"] = code
    return go(request.headers.get("referer") or "/")


# ---------- inloggen ----------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render(request, "login.html")


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    c = db.query(Company).filter(Company.email == email.strip().lower()).first()
    if not c or c.is_demo or not check_pw(password, c.password_hash):
        return render(request, "login.html", error=t("wrong_login", ui_lang(request)), email=email)
    request.session.clear()
    request.session["cid"] = c.id
    return go("/offertes")


@app.get("/aanmelden", response_class=HTMLResponse)
def register_page(request: Request):
    return render(request, "register.html")


@app.post("/aanmelden")
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...),
             country: str = Form(""), lang: str = Form("nl"), db=Depends(get_db)):
    email = email.strip().lower()
    ul = lang if lang in LANGS else ui_lang(request)
    if len(password) < 8:
        return render(request, "register.html", lang=ul, error=t("pw_short", ul), name=name, email=email)
    if db.query(Company).filter(Company.email == email).first():
        return render(request, "register.html", lang=ul, error=t("email_taken", ul), name=name, email=email)
    vat = {"Deutschland": 19.0, "France": 20.0}.get(country, 21.0)
    c = Company(email=email, password_hash=hash_pw(password), name=name.strip(), country=country.strip(),
                lang=ul, default_vat=vat)
    db.add(c)
    db.commit()
    request.session.clear()
    request.session["cid"] = c.id
    return go("/instellingen?welkom=1")


@app.get("/demo")
def demo(request: Request, db=Depends(get_db)):
    c = ensure_demo(db)
    lang = request.session.get("lang") or ui_lang(request)
    request.session.clear()
    request.session["cid"] = c.id
    request.session["demo_lang"] = lang
    return go("/offertes")


@app.get("/uitloggen")
def logout(request: Request):
    lang = request.session.get("lang")
    request.session.clear()
    if lang:
        request.session["lang"] = lang
    return go("/login")


def company_ctx(request: Request, db):
    c = need_company(request, db)
    lang = request.session.get("demo_lang") if c.is_demo else c.lang
    return c, (lang if lang in LANGS else "nl")


# ---------- offertes ----------
@app.get("/offertes", response_class=HTMLResponse)
def quotes_list(request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    quotes = db.query(Quote).filter(Quote.company_id == c.id).order_by(Quote.created_at.desc()).all()
    rows, open_n, open_value, acc_n, acc_value, decided, won = [], 0, 0.0, 0, 0.0, 0, 0
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for q in quotes:
        tot = totals(lines_of(q))
        rows.append((q, tot))
        if q.status in ("concept", "verstuurd"):
            open_n += 1
            open_value += tot["total"]
        if q.status in ("akkoord", "afgewezen"):
            decided += 1
            if q.status == "akkoord":
                won += 1
        if q.status == "akkoord" and q.decided_at and q.decided_at >= month_start:
            acc_n += 1
            acc_value += tot["total"]
    stats = {"open_n": open_n, "open_value": open_value, "acc_n": acc_n, "acc_value": acc_value,
             "rate": round(100 * won / decided) if decided else None}
    return render(request, "quotes.html", c, lang, rows=rows, stats=stats)


@app.get("/nieuw", response_class=HTMLResponse)
def new_page(request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    n_products = db.query(Product).filter(Product.company_id == c.id).count()
    return render(request, "new.html", c, lang, n_products=n_products, qlang=lang)


@app.post("/nieuw")
def new_quote(request: Request, wish: str = Form(...), qlang: str = Form("nl"), db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    via_js = request.headers.get("x-nocturo") == "1"  # wachtscherm wacht zelf op het antwoord

    def fout(msg, url=None):
        if via_js:
            return JSONResponse({"error": msg, "url": url})
        if url:
            flash(request, msg, "fout")
            return go(url)
        n_products = db.query(Product).filter(Product.company_id == c.id).count()
        return render(request, "new.html", c, lang, n_products=n_products, qlang=qlang, wish=wish, error=msg)

    if not c.access_ok():
        return fout(t("trial_over", lang), "/offertes")
    wish = (wish or "").strip()[:8000]
    if not wish:
        return fout(t("what_wants", lang))
    qlang = qlang if qlang in LANGS else lang
    ip = request.client.host if request.client else "?"
    if not ai_allowed(f"demo:{ip}" if c.is_demo else f"c:{c.id}", 8 if c.is_demo else 120):
        return fout(t("ai_error", lang) + " (limit)")
    products = db.query(Product).filter(Product.company_id == c.id).order_by(Product.name).all()
    try:
        data = ai.make_quote(c, products, wish, qlang)
    except ai.AIError as e:
        print("AI-fout:", e, flush=True)
        return fout(t("ai_error", lang))
    now = datetime.utcnow()
    q = Quote(
        company_id=c.id, number=f"{c.prefix or ''}{now.year}-{c.next_number:03d}", status="concept", lang=qlang,
        customer_name=data["customer_name"], customer_company=data["customer_company"],
        customer_email=data["customer_email"], customer_address=data["customer_address"],
        title=data["title"], intro=data["intro"], closing=data["closing"],
        lines_json=json.dumps(data["lines"], ensure_ascii=False),
        notes_json=json.dumps(data["notes"], ensure_ascii=False),
        request_text=wish, date=now, valid_until=now + timedelta(days=c.validity_days or 30),
    )
    c.next_number = (c.next_number or 1) + 1
    db.add(q)
    db.commit()
    if via_js:
        return JSONResponse({"url": f"/offerte/{q.id}"})
    return go(f"/offerte/{q.id}")


@app.get("/offerte/{qid}", response_class=HTMLResponse)
def quote_edit(qid: int, request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    lines = lines_of(q)
    products = db.query(Product).filter(Product.company_id == c.id).order_by(Product.name).all()
    return render(request, "edit.html", c, lang, q=q, lines=lines, notes=notes_of(q), tot=totals(lines),
                  statuses=STATUSES, public_url=f"{base_url(request)}/q/{q.token}",
                  products_json=json.dumps([{"name": p.name, "unit": p.unit, "price": p.price, "vat": p.vat}
                                            for p in products], ensure_ascii=False))


@app.post("/offerte/{qid}")
def quote_save(qid: int, request: Request, db=Depends(get_db),
               customer_name: str = Form(""), customer_company: str = Form(""), customer_email: str = Form(""),
               customer_address: str = Form(""), title: str = Form(""), intro: str = Form(""),
               closing: str = Form(""), lines_json: str = Form("[]"), valid_until: str = Form(""),
               qlang: str = Form("nl"), next: str = Form("")):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    try:
        raw = json.loads(lines_json)
    except ValueError:
        raw = []
    lines = []
    for ln in raw if isinstance(raw, list) else []:
        desc = str(ln.get("description") or "").strip()
        if not desc:
            continue
        price = ln.get("price")
        price = None if price in (None, "") else round(parse_float(price), 2)
        lines.append({"description": desc[:500], "qty": parse_float(ln.get("qty"), 1.0),
                      "unit": str(ln.get("unit") or "")[:50], "price": price,
                      "vat": parse_float(ln.get("vat"), c.default_vat)})
    q.customer_name, q.customer_company = customer_name.strip(), customer_company.strip()
    q.customer_email, q.customer_address = customer_email.strip(), customer_address.strip()
    q.title, q.intro, q.closing = title.strip(), intro.strip(), closing.strip()
    q.lines_json = json.dumps(lines, ensure_ascii=False)
    q.lang = qlang if qlang in LANGS else q.lang
    try:
        q.valid_until = datetime.strptime(valid_until, "%Y-%m-%d") if valid_until else None
    except ValueError:
        pass
    db.commit()
    if next == "pdf":
        return go(f"/offerte/{q.id}/pdf")
    if next == "send":
        return go(f"/offerte/{q.id}/versturen")
    flash(request, t("saved", lang))
    return go(f"/offerte/{q.id}")


@app.post("/offerte/{qid}/status")
def quote_status(qid: int, request: Request, status: str = Form(...), db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    if status in STATUSES:
        q.status = status
        if status in ("akkoord", "afgewezen") and not q.decided_at:
            q.decided_at = datetime.utcnow()
        if status in ("concept", "verstuurd"):
            q.decided_at, q.decided_by = None, ""
        db.commit()
    return go(f"/offerte/{q.id}")


@app.post("/offerte/{qid}/verwijderen")
def quote_delete(qid: int, request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    db.delete(q)
    db.commit()
    return go("/offertes")


@app.post("/offerte/{qid}/kopie")
def quote_copy(qid: int, request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    now = datetime.utcnow()
    n = Quote(company_id=c.id, number=f"{c.prefix or ''}{now.year}-{c.next_number:03d}", lang=q.lang,
              customer_name=q.customer_name, customer_company=q.customer_company, customer_email=q.customer_email,
              customer_address=q.customer_address, title=q.title, intro=q.intro, closing=q.closing,
              lines_json=q.lines_json, notes_json="[]", request_text=q.request_text, date=now,
              valid_until=now + timedelta(days=c.validity_days or 30))
    c.next_number = (c.next_number or 1) + 1
    db.add(n)
    db.commit()
    return go(f"/offerte/{n.id}")


@app.get("/offerte/{qid}/pdf")
def quote_pdf_route(qid: int, request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    return Response(quote_pdf(request, q), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{pdf_name(q)}"'})


@app.get("/offerte/{qid}/versturen", response_class=HTMLResponse)
def send_page(qid: int, request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    url = f"{base_url(request)}/q/{q.token}"
    greet = q.customer_name.split(" ")[0] if q.customer_name else ""
    subject = d("mail_subject", q.lang, n=q.number, c=c.name)
    body = d("mail_body", q.lang, k=greet, n=q.number, l=url, c=c.name)
    return render(request, "send.html", c, lang, q=q, subject=subject, body=body, mail_ok=mail_ready(),
                  public_url=url)


@app.post("/offerte/{qid}/versturen")
def send_quote(qid: int, request: Request, to: str = Form(...), subject: str = Form(...), body: str = Form(...),
               db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    q = own_quote(db, c, qid)
    if c.is_demo:
        flash(request, t("demo_no_send", lang), "fout")
        return go(f"/offerte/{q.id}")
    if not c.access_ok():
        flash(request, t("trial_over", lang), "fout")
        return go(f"/offerte/{q.id}")
    if not mail_ready():
        flash(request, t("mail_not_set", lang), "fout")
        return go(f"/offerte/{q.id}")
    try:
        send_quote_mail(c, to.strip(), subject.strip(), body, quote_pdf(request, q), pdf_name(q))
    except Exception as e:
        print("Mailfout:", e, flush=True)
        flash(request, f"{t('send_failed', lang)} {e}", "fout")
        return go(f"/offerte/{q.id}/versturen")
    q.status = "verstuurd" if q.status == "concept" else q.status
    q.sent_at = datetime.utcnow()
    if not q.customer_email:
        q.customer_email = to.strip()
    db.commit()
    flash(request, t("sent_ok", lang))
    return go(f"/offerte/{q.id}")


# ---------- prijslijst ----------
@app.get("/prijslijst", response_class=HTMLResponse)
def products_page(request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    products = db.query(Product).filter(Product.company_id == c.id).order_by(Product.name).all()
    return render(request, "products.html", c, lang, products=products)


def demo_block(request, c, lang):
    if c.is_demo:
        flash(request, t("demo_banner", lang), "fout")
        return True
    return False


@app.post("/prijslijst/nieuw")
def product_add(request: Request, name: str = Form(...), description: str = Form(""), unit: str = Form(""),
                price: str = Form("0"), vat: str = Form(""), db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    if demo_block(request, c, lang):
        return go("/prijslijst")
    if name.strip():
        db.add(Product(company_id=c.id, name=name.strip()[:255], description=description.strip(),
                       unit=unit.strip()[:50], price=round(parse_float(price), 2),
                       vat=parse_float(vat, c.default_vat) if vat.strip() else c.default_vat))
        db.commit()
    return go("/prijslijst")


@app.post("/prijslijst/{pid}")
def product_update(pid: int, request: Request, name: str = Form(...), description: str = Form(""),
                   unit: str = Form(""), price: str = Form("0"), vat: str = Form("21"), db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    if demo_block(request, c, lang):
        return go("/prijslijst")
    p = db.get(Product, pid)
    if not p or p.company_id != c.id:
        raise HTTPException(404)
    p.name, p.description, p.unit = name.strip()[:255], description.strip(), unit.strip()[:50]
    p.price, p.vat = round(parse_float(price), 2), parse_float(vat, c.default_vat)
    db.commit()
    flash(request, t("saved", lang))
    return go("/prijslijst")


@app.post("/prijslijst/{pid}/verwijderen")
def product_delete(pid: int, request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    if demo_block(request, c, lang):
        return go("/prijslijst")
    p = db.get(Product, pid)
    if p and p.company_id == c.id:
        db.delete(p)
        db.commit()
    return go("/prijslijst")


@app.post("/prijslijst-inlezen")
def product_import(request: Request, text: str = Form(...), db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    if demo_block(request, c, lang):
        return go("/prijslijst")
    if not ai_allowed(f"c:{c.id}", 120):
        flash(request, t("ai_error", lang), "fout")
        return go("/prijslijst")
    try:
        items = ai.import_pricelist(text[:20000], c)
    except ai.AIError as e:
        print("AI-fout import:", e, flush=True)
        flash(request, t("ai_error", lang), "fout")
        return go("/prijslijst")
    for it in items:
        db.add(Product(company_id=c.id, **it))
    db.commit()
    flash(request, f"{len(items)} {t('imported', lang)}")
    return go("/prijslijst")


# ---------- instellingen ----------
@app.get("/instellingen", response_class=HTMLResponse)
def settings_page(request: Request, db=Depends(get_db)):
    c, lang = company_ctx(request, db)
    return render(request, "settings.html", c, lang, welcome=request.query_params.get("welkom") == "1")


@app.post("/instellingen")
async def settings_save(request: Request, db=Depends(get_db), logo: UploadFile | None = File(None)):
    c, lang = company_ctx(request, db)
    if demo_block(request, c, lang):
        return go("/instellingen")
    form = await request.form()
    for f in ["name", "address", "postcode_city", "country", "phone", "website", "coc", "vat_no", "iban",
              "prefix", "terms"]:
        if f in form:
            setattr(c, f, str(form.get(f) or "").strip())
    if not c.name:
        c.name = "—"
    acc = str(form.get("accent") or "")
    if len(acc) == 7 and acc.startswith("#"):
        c.accent = acc
    c.default_vat = parse_float(form.get("default_vat"), c.default_vat)
    c.validity_days = int(parse_float(form.get("validity_days"), c.validity_days or 30)) or 30
    if form.get("lang") in LANGS:
        c.lang = form.get("lang")
    if form.get("remove_logo") == "1":
        c.logo_data = ""
    if logo is not None and logo.filename:
        data = await logo.read()
        if len(data) <= 1_000_000 and (logo.content_type or "").startswith("image/"):
            c.logo_data = f"data:{logo.content_type};base64," + base64.b64encode(data).decode()
    db.commit()
    flash(request, t("saved", c.lang))
    return go("/instellingen")


# ---------- klantpagina ----------
@app.get("/q/{token}", response_class=HTMLResponse)
def public_quote(token: str, request: Request, db=Depends(get_db)):
    q = db.query(Quote).filter(Quote.token == token).first()
    if not q:
        raise HTTPException(404)
    lines = lines_of(q)
    ql = q.lang or "nl"
    return render(request, "public.html", None, ql, q=q, co=q.company, lines=lines, tot=totals(lines),
                  D=lambda k, **kw: d(k, ql, **kw), done=request.query_params.get("klaar"))


@app.post("/q/{token}")
def public_decide(token: str, request: Request, action: str = Form(...), name: str = Form(""), db=Depends(get_db)):
    q = db.query(Quote).filter(Quote.token == token).first()
    if not q:
        raise HTTPException(404)
    if q.status not in ("akkoord", "afgewezen"):
        q.status = "akkoord" if action == "akkoord" else "afgewezen"
        q.decided_at = datetime.utcnow()
        q.decided_by = name.strip()[:255] or q.customer_name
        db.commit()
    return go(f"/q/{token}?klaar=1")


@app.get("/q/{token}/pdf")
def public_pdf(token: str, request: Request, db=Depends(get_db)):
    q = db.query(Quote).filter(Quote.token == token).first()
    if not q:
        raise HTTPException(404)
    return Response(quote_pdf(request, q), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{pdf_name(q)}"'})


# ---------- beheer (alleen Marcel) ----------
def need_admin(request, db):
    c = need_company(request, db)
    if not ADMIN_EMAIL or c.email != ADMIN_EMAIL:
        raise HTTPException(404)
    return c


@app.get("/beheer", response_class=HTMLResponse)
def admin_page(request: Request, db=Depends(get_db)):
    c = need_admin(request, db)
    companies = db.query(Company).filter(Company.is_demo == False).order_by(Company.created_at.desc()).all()  # noqa: E712
    counts = {x.id: db.query(Quote).filter(Quote.company_id == x.id).count() for x in companies}
    return render(request, "admin.html", c, c.lang, companies=companies, counts=counts, now=datetime.utcnow())


@app.post("/beheer/{cid}")
def admin_action(cid: int, request: Request, action: str = Form(...), db=Depends(get_db)):
    need_admin(request, db)
    x = db.get(Company, cid)
    if not x or x.is_demo:
        raise HTTPException(404)
    now = datetime.utcnow()
    if action == "maand":
        start = x.paid_until if x.paid_until and x.paid_until > now else now
        x.paid_until = start + timedelta(days=31)
    elif action == "proef":
        x.trial_ends = max(x.trial_ends or now, now) + timedelta(days=14)
    elif action == "aanuit":
        x.is_active = not x.is_active
    db.commit()
    return go("/beheer")
