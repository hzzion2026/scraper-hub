"""
Extractor — scrapes fields from pages using CSS selectors + fallback logic.
Supports scoped extraction within a specific element (card).
"""
import re
from typing import Optional
from playwright.sync_api import Page


class Extractor:
    """Generic field extractor with CSS selectors and regex fallbacks."""

    PHONE_PATTERN = re.compile(
        r'(?:\+?\d{1,3}[-\s.]?)?\(?\d{2,4}\)?[-\s.]?\d{3,4}[-\s.]?\d{3,4}'
    )
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    def __init__(self, page: Page, field_selectors: dict[str, str]):
        self.page = page
        self.field_selectors = field_selectors

    def extract_field(self, field_name: str, selector: str, scope=None) -> Optional[str]:
        """Extract a single field by CSS selector, optionally scoped to a parent element."""
        if not selector:
            return None
        try:
            root = scope or self.page
            el = root.query_selector(selector)
            if el:
                text = el.inner_text().strip()
                return text if text else None
        except Exception:
            pass
        return None

    def extract_email_from_body(self, text: str = None) -> Optional[str]:
        """Scan text for email patterns."""
        if text:
            match = self.EMAIL_PATTERN.search(text)
            return match.group(0) if match else None
        body = self.page.inner_text("body")
        match = self.EMAIL_PATTERN.search(body)
        return match.group(0) if match else None

    def extract_phone_from_body(self, text: str = None) -> Optional[str]:
        """Scan text for phone patterns."""
        if text:
            match = self.PHONE_PATTERN.search(text)
            return match.group(0) if match else None
        body = self.page.inner_text("body")
        match = self.PHONE_PATTERN.search(body)
        return match.group(0) if match else None

    def extract_all(self, scope=None) -> dict[str, Optional[str]]:
        """Extract all configured fields from a page or scoped element."""
        card_text = scope.inner_text() if scope else None

        record = {}
        for field_name, selector in self.field_selectors.items():
            value = self.extract_field(field_name, selector, scope=scope)
            record[field_name] = value

        # Fallback: if email/phone selectors didn't work, scan element text
        if not record.get("email") and card_text:
            record["email"] = self.extract_email_from_body(card_text)
        elif not record.get("email"):
            record["email"] = self.extract_email_from_body()

        if not record.get("phone") and card_text:
            record["phone"] = self.extract_phone_from_body(card_text)
        elif not record.get("phone"):
            record["phone"] = self.extract_phone_from_body()

        return record
