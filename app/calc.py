import json


def lines_of(quote) -> list:
    try:
        return json.loads(quote.lines_json or "[]")
    except ValueError:
        return []


def notes_of(quote) -> list:
    try:
        return json.loads(quote.notes_json or "[]")
    except ValueError:
        return []


def totals(lines: list) -> dict:
    """Subtotaal, btw per tarief en totaal. Regels zonder prijs tellen niet mee."""
    sub = 0.0
    vat_groups = {}
    missing = 0
    for ln in lines:
        if ln.get("price") is None:
            missing += 1
            continue
        amount = round(float(ln.get("qty") or 0) * float(ln["price"]), 2)
        sub += amount
        rate = float(ln.get("vat") or 0)
        vat_groups[rate] = vat_groups.get(rate, 0.0) + amount
    vat_lines = [(rate, round(base * rate / 100, 2)) for rate, base in sorted(vat_groups.items()) if rate]
    vat_total = sum(v for _, v in vat_lines)
    return {
        "subtotal": round(sub, 2),
        "vat_lines": vat_lines,
        "total": round(sub + vat_total, 2),
        "missing": missing,
    }
