"""Extract amount, date, merchant and category hints from receipt / UPI bill text."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

AMOUNT_PATTERNS = [
    re.compile(r"(?:grand\s*total|amount\s*paid|total\s*paid|net\s*paid|paid)\s*[:\-]?\s*(?:inr|rs\.?|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?)", re.I),
    re.compile(r"(?:total|amount)\s*[:\-]?\s*(?:inr|rs\.?|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?)", re.I),
    re.compile(r"(?:₹|rs\.?|inr)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?)", re.I),
]

DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"),
    re.compile(r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})\b", re.I),
    re.compile(r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"),
]

MERCHANT_PATTERNS = [
    re.compile(r"(?:paid\s*to|payee|merchant|billed\s*to|to)\s*[:\-]?\s*(.+)", re.I),
    re.compile(r"(?:from)\s*[:\-]?\s*(.+)", re.I),
]

CATEGORY_KEYWORDS = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "hotel", "food", "dining", "pizza", "burger", "domino", "kfc", "mcdonald"],
    "Groceries": ["grocery", "supermarket", "bigbasket", "blinkit", "zepto", "dmart", "reliance fresh", "more supermarket"],
    "Travel": ["uber", "ola", "rapido", "irctc", "flight", "indigo", "air india", "petrol", "fuel", "metro", "bus", "cab"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho", "shopping", "mall", "store"],
    "Education": ["fee", "tuition", "course", "udemy", "byju", "school", "college", "book"],
    "Entertainment": ["netflix", "spotify", "prime", "hotstar", "bookmyshow", "movie", "game"],
    "Bills": ["electricity", "water", "wifi", "broadband", "airtel", "jio", "bsnl", "recharge", "gas"],
    "Health": ["pharmacy", "apollo", "hospital", "clinic", "medicine", "medplus", "1mg"],
    "Rent": ["rent", "landlord", "pg ", "hostel"],
}

NOISE = re.compile(
    r"google pay|phonepe|paytm|bhim|upi|transaction successful|paid successfully|thank you|gstin|invoice|receipt|original",
    re.I,
)


def _to_float(raw: str) -> float | None:
    try:
        return round(float(raw.replace(",", "")), 2)
    except ValueError:
        return None


def _parse_date(raw: str) -> str | None:
    raw = raw.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def infer_category(text: str) -> str:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for category, words in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for word in words if word in lowered)
    best = max(scores, key=scores.get)
    return best if scores[best] else "Other"


def extract_merchant(text: str) -> str:
    for pattern in MERCHANT_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip(" :-|")
            candidate = re.split(r"[\n|]", candidate)[0].strip()
            if 2 < len(candidate) < 48 and not NOISE.search(candidate):
                return candidate.title()
    for line in text.splitlines():
        clean = line.strip(" :-*|")
        if 3 < len(clean) < 42 and not NOISE.search(clean) and not re.search(r"\d{3,}", clean):
            return clean.title()
    return "Scanned merchant"


def parse_receipt_text(text: str) -> dict[str, Any]:
    compact = text.replace("\r", "\n")
    amount = None
    for pattern in AMOUNT_PATTERNS:
        match = pattern.search(compact)
        if match:
            amount = _to_float(match.group(1))
            if amount and amount > 0:
                break

    if amount is None:
        numbers = [_to_float(n) for n in re.findall(r"[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+\.[0-9]{2}", compact)]
        numbers = [n for n in numbers if n and 1 <= n <= 1_000_000]
        amount = max(numbers) if numbers else None

    date_value = datetime.now().strftime("%Y-%m-%d")
    for pattern in DATE_PATTERNS:
        match = pattern.search(compact)
        if match:
            parsed = _parse_date(match.group(1))
            if parsed:
                date_value = parsed
                break

    merchant = extract_merchant(compact)
    category = infer_category(compact + " " + merchant)
    payment = "UPI" if re.search(r"\bupi\b|gpay|google pay|phonepe|paytm", compact, re.I) else "Card" if re.search(r"card|visa|mastercard", compact, re.I) else "Cash"

    return {
        "amount": amount or 0,
        "date": date_value,
        "merchant": merchant,
        "category": category,
        "payment_method": payment,
        "note": f"Imported from receipt - {merchant}",
        "raw_text": compact[:4000],
    }
