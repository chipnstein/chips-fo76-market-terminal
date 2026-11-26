import re
from datetime import datetime, timezone


def _parse_number(num_str: str) -> float:
    """Converts '1.5k', '1,5k', '20k', '500' into a float."""
    s = num_str.lower().replace(" ", "")
    mult = 1.0
    if s.endswith("k"):
        mult = 1000.0
        s = s[:-1]
    if "," in s and mult == 1000.0:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    return float(s) * mult


def _detect_platform(title: str, flair: str = "") -> str | None:
    """Extracts 'PC', 'PS', or 'XB' from the post title or flair."""
    combined = f"{title} {flair}".upper()
    if re.search(r"[\[\(]\s*PC\s*[\]\)]|\bPC\s+TRADE\b", combined):
        return "PC"
    if re.search(r"[\[\(]\s*PS[45]?\s*[\]\)]|\bPS\s+TRADE\b", combined):
        return "PS"
    if re.search(r"[\[\(]\s*XB[1X]?\s*[\]\)]|\bXB\s+TRADE\b", combined):
        return "XB"
    return None


def _extract_currency_side(text: str) -> tuple[float | None, str] | None:
    """
    Checks if a H:/W: side is purely a currency/offer statement.
    Returns (numeric_price_or_None, currency) or None if it looks like an item.
    """
    cleaned = text.strip()
    lower = cleaned.lower()

    # Exact numeric Leaders: "500 leaders", "1.3k L", "50L"
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?\s*k?)\s*(?:l|leaders?|leader\s+bobbleheads?)", lower)
    if m:
        return _parse_number(m.group(1)), "L"

    # Exact numeric Caps: "20k caps", "40000c", "15k"
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?\s*k?)\s*(?:c|caps?)", lower)
    if m:
        return _parse_number(m.group(1)), "c"

    # Unpriced currency or offers: "leaders", "caps", "offers"
    if re.fullmatch(r"(?:leaders?|leader\s+bobbleheads?)", lower):
        return None, "L"
    if re.fullmatch(r"(?:caps?)", lower):
        return None, "c"
    if re.fullmatch(r"(?:offers?|good\s+offers?)", lower):
        return None, "OFFER"

    return None


def _split_hw(title: str) -> tuple[str, str] | None:
    """Splits a trade title into (have_text, want_text), supporting H:/W: or W:/H: order."""
    # Strip leading platform tag like [PC], [PS5], (Xb1)
    cleaned = re.sub(r"^\s*[\[\(]\s*(?:PC|PS[45]?|XB[1X]?)\s*[\]\)]\s*", "", title, flags=re.IGNORECASE)

    # Order 1: H: ... W: ...
    m = re.search(r"\bH\s*:\s*(.+?)\s+\bW\s*:\s*(.+)$", cleaned, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Order 2: W: ... H: ...
    m = re.search(r"\bW\s*:\s*(.+?)\s+\bH\s*:\s*(.+)$", cleaned, flags=re.IGNORECASE)
    if m:
        return m.group(2).strip(), m.group(1).strip()

    return None


def parse_trade_post(
    post_id: str,
    title: str,
    flair: str = "",
    created_utc: str | None = None,
) -> dict | None:
    """
    Parses a single r/Market76 post into a structured trade dict ready for SQLite.
    Returns None if the post isn't a recognizable currency/offer trade.
    """
    platform = _detect_platform(title, flair)
    if not platform:
        return None

    hw = _split_hw(title)
    if not hw:
        return None

    have_text, want_text = hw
    have_curr = _extract_currency_side(have_text)
    want_curr = _extract_currency_side(want_text)

    # Skip currency-for-currency (e.g., "H: 40k caps W: 40 Leaders") or pure item-for-item swaps
    if (have_curr and want_curr) or (not have_curr and not want_curr):
        return None

    if have_curr:
        # Poster HAS currency and WANTS an item -> BUY demand
        price, currency = have_curr
        direction = "BUY"
        item_name = want_text
    else:
        # Poster HAS an item and WANTS currency/offers -> SELL supply
        price, currency = want_curr
        direction = "SELL"
        item_name = have_text

    timestamp = created_utc or datetime.now(timezone.utc).isoformat()

    return {
        "post_id": post_id,
        "created_utc": timestamp,
        "platform": platform,
        "direction": direction,
        "item_name": item_name.strip(" .,-"),
        "price": price,
        "currency": currency,
        "raw_title": title,
    }


if __name__ == "__main__":
    # Quick local sanity test against real-style r/Market76 titles
    samples = [
        ("t3_001", "[PC] H: 3500 Leaders W: Clean Pitman Mask", "PC Trade"),
        ("t3_002", "[PS] H: Weenie Wagon Plan W: 20k Caps", "PS Trade"),
        ("t3_003", "(Xb1) H: leaders W: 5x Pin-Pointers", "XB Trade"),
        ("t3_004", "[PC] W: T60 Headlamp Plan H: 650 Leaders", "PC Trade"),
        ("t3_005", "[PC] H: Last Stand W: Offers", "PC Trade"),
        ("t3_006", "[PC] H: 40k caps W: 40 Leaders", "PC Trade"),  # Should be skipped
    ]

    for pid, title, flair in samples:
        parsed = parse_trade_post(pid, title, flair)
        print(f"{pid} -> {parsed}")