"""
Exporter — saves scraped data as CSV, JSON, or Excel.
"""
import csv
import json
from pathlib import Path


def export_csv(records: list[dict], path: str | Path):
    """Export to CSV."""
    if not records:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def export_json(records: list[dict], path: str | Path):
    """Export to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def export_excel(records: list[dict], path: str | Path):
    """Export to Excel (.xlsx)."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    if records:
        ws.append(list(records[0].keys()))
        for rec in records:
            ws.append(list(rec.values()))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))


EXPORTERS = {
    "csv": export_csv,
    "json": export_json,
    "excel": export_excel,
}
