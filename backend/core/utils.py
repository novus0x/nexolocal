########## Modules ##########
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone, timedelta, date, time

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
