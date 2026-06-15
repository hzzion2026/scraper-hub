"""
Validator & deduplicator — email/phone format checks, duplicate removal.
"""
import re
from typing import Optional
import phonenumbers


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_email(email: Optional[str]) -> bool:
    if not email or not email.strip():
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_phone(phone: Optional[str]) -> bool:
    """Basic phone validation — checks length and digits."""
    if not phone or not phone.strip():
        return False
    digits = re.sub(r'\D', '', phone)
    return 7 <= len(digits) <= 15


def normalize_phone(phone: str) -> str:
    """Strip non-digit chars but preserve leading +"""
    phone = phone.strip()
    if phone.startswith("+"):
        return "+" + re.sub(r'\D', '', phone[1:])
    return re.sub(r'\D', '', phone)


def deduplicate(records: list[dict], keys: list[str] | None = None) -> list[dict]:
    """Remove duplicate records based on key fields."""
    if keys is None:
        keys = ["business_name", "email", "phone"]

    seen: set[tuple] = set()
    unique: list[dict] = []
    for rec in records:
        sig = tuple(str(rec.get(k, "")).strip().lower() for k in keys)
        if sig and sig not in seen:
            seen.add(sig)
            unique.append(rec)
    return unique


class DataValidator:
    @staticmethod
    def validate_record(record: dict) -> dict:
        """Returns record with validated + normalized fields."""
        result = dict(record)

        email = record.get("email", "")
        result["email_valid"] = validate_email(email)

        phone = record.get("phone", "")
        result["phone_normalized"] = normalize_phone(phone) if phone else ""
        result["phone_valid"] = validate_phone(phone)

        return result
