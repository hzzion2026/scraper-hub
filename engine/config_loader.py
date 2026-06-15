"""
Config loader — reads YAML target configs and validates structure.
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml


class TargetConfig(BaseModel):
    name: str
    start_url: str
    pagination: Optional[str] = None  # CSS selector or JS 'next page' logic
    max_pages: int = 1
    scroll_pause_sec: float = 1.0

    # Field extraction rules
    fields: dict[str, str] = Field(default_factory=lambda: {
        "business_name": "",
        "trade_category": "",
        "contact_name": "",
        "email": "",
        "phone": "",
        "city": "",
    })

    # Anti-detection
    use_proxy: bool = False
    proxy_list: list[str] = []
    headless: bool = True
    human_delay: tuple[float, float] = (0.5, 2.0)

    # Output
    output_format: str = "csv"  # csv | json | excel
    output_name: Optional[str] = None


def load_config(path: str) -> TargetConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return TargetConfig(**raw)
