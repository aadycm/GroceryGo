import re
from email_validator import validate_email, EmailNotValidError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def require_fields(payload, fields):
    """Returns a list of missing field names."""
    if not payload:
        return list(fields)
    return [f for f in fields if payload.get(f) in (None, "")]


def is_valid_phone(phone):
    return bool(re.fullmatch(r"[0-9+\-\s]{7,20}", phone or ""))
