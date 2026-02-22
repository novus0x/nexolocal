########## Modules ##########
import zstandard

from math import isfinite
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta, date, time

########## Variables ##########
ZSTD_LEVEL = 3

########## Time Ago ##########
def time_ago(dt):
    now = datetime.now(timezone.utc)
    delta = now - dt

    seconds = int(delta.total_seconds())
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    if seconds < 60:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    if hours < 24:
        return f"{hours} h ago"
    return f"{days} days ago"

########## Is Int ##########
def is_int(value):
    try:
        dec = Decimal(str(value))
        if dec % 1 == 0:
            return int(dec)
        return None
    except (InvalidOperation, TypeError):
        return None

########## Is Float ##########
def is_float(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None

########## Is date yyyy_mm_dd ##########
def is_date_yyyy_mm_dd(value: str):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

########## Date Label ##########
def date_label(dt: datetime):
    today = datetime.now().date()
    items_date = dt.date()

    if items_date == today:
        return "TODAY"
    elif items_date == today - timedelta(days=1):
        return "YESTERDAY"
    else:
        return items_date.strftime("%B %d, %Y").upper()

########## Pagination ##########
def pagination(total_items, limit, offset):
    if limit <= 0:
        limit = 15

    total_pages = (total_items + limit - 1) // limit

    return {
        "next": offset + limit < total_items,
        "back": offset > 0,
        "q_pages": total_pages
    }

########## Normalize Search ##########
def normalize_search(q: str | None) -> str | None:
    if not q:
        return None
    q = q.strip()
    return q if len(q) >= 2 else None

########## Validate Same Day ##########
def validate_not_same_day(reception_date: str):
    now = datetime.now(timezone.utc)

    if not reception_date:
        return False 
    
    rec_date = datetime.strptime(reception_date, "%Y-%m-%d").date()

    if rec_date == date.today():
        return False

    custom_dt = datetime.combine(rec_date, time.min, tzinfo=timezone.utc)
    
    return custom_dt

########## To Decimal - Fix: floating point error ##########
def to_decimal(value, default = None):
    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    if isinstance(value, bool):
        return default

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, float):
        if not isfinite(value):
            return default

        return Decimal(str(value))

    if isinstance(value, str):
        raw = value.strip().replace(",", ".")
        if raw == "":
            return default

        try:
            return Decimal(raw)
        except InvalidOperation:
            return default

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default

########## To Decimal Or Zero ##########
def to_decimal_or_zero(value):
    return to_decimal(value, Decimal("0"))

########## To Money ##########
def to_money(value, default = Decimal("0.00")):
    dec = to_decimal(value, default)

    if dec is None:
        return None

    return dec.quantize(Decimal("0.01"), ROUND_HALF_UP)

########## ZSTD Compression ##########
def zstd_compression(data) -> bytes:
    ### Validation ###
    if data is None:
        return None
    
    if isinstance(data, str):
        data = data.encode("utf-8")

    ### Compression ###
    compressor = zstandard.ZstdCompressor(level=ZSTD_LEVEL)

    return compressor.compress(data)

########## ZSTD Decompression ##########
def zstd_decompress(data: bytes) -> str:
    ### Validation ###
    if data is None:
        return None

    ### Decompression ##
    decompressor = zstandard.ZstdDecompressor()

    return decompressor.decompress(data).decode("utf-8")
