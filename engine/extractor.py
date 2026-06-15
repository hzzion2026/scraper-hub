"""
Extractor — scrapes fields from pages using CSS selectors + fallback logic.
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

    def extract_field(self, field_name: str, selector: str) -> Optional[str]:
        """Extract a single field by CSS selector, with regex fallback for email/phone."""
        if not selector:
            return None

        try:
            el = self.page.query_selector(selector)
            if el:
                text = el.inner_text().strip()
                return text if text else None
        except Exception:
            pass
        return None

    def extract_email_from_body(self) -> Optional[str]:
        """Fallback: scan entire page text for email patterns."""
        body = self.page.inner_text("body")
        match = self.EMAIL_PATTERN.search(body)
        return match.group(0) if match else None

    def extract_phone_from_body(self) -> Optional[str]:
        """Fallback: scan entire page text for phone patterns."""
        body = self.page.inner_text("body")
        match = self.PHONE_PATTERN.search(body)
        return match.group(0) if match else None

    def extract_all(self) -> dict[str, Optional[str]]:
        """Extract all configured fields from the current page."""
        record = {}
        for field_name, selector in self.field_selectors.items():
            value = self.extract_field(field_name, selector)
            record[field_name] = value

        # Fallback: if email/phone selectors didn't work, scan page body
        if not record.get("email"):
            record["email"] = self.extract_email_from_body()
        if not record.get("phone"):
            record["phone"] = self.extract_phone_from_body()

        return record
