#!/usr/bin/env python3
"""
ScraperHub CLI — one command to scrape business directories.
"""
import sys
from pathlib import Path
import click
from loguru import logger

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from engine.config_loader import load_config
from engine.scraper import Scraper

logger.remove()
logger.add(sys.stderr, format="<level>{level: <8}</level> | <level>{message}</level>", colorize=True)


@click.group()
def cli():
    """ScraperHub — deploy-ready web scraping system."""


@cli.command()
@click.argument("config", type=click.Path(exists=True))
def run(config):
    """Run a scrape job from a YAML config file."""
    cfg = load_config(config)
    scraper = Scraper(cfg)
    records = scraper.run()
    click.echo(f"\n✅ Done! {len(records)} records scraped.")


@cli.command()
def demo():
    """Run a demo scrape on a sample config (no external dependency)."""
    click.echo("""
╔══════════════════════════════════════╗
║       ScraperHub — Demo Mode         ║
╚══════════════════════════════════════╝

ScraperHub is ready! To run a real scrape:

  1. Edit a config file in configs/
  2. Run: python cli.py run configs/your_target.yml

Sample configs included:
  - configs/example.yml

System capabilities:
  ✓ Playwright Stealth (anti-detection)
  ✓ Proxy rotation
  ✓ Human-like delays
  ✓ Email/phone validation
  ✓ Deduplication
  ✓ CSV / JSON / Excel export

Need help?  python cli.py run --help
""")


@cli.command()
@click.option("--records", default=100, help="Number of sample records to generate")
def simulate(records):
    """Generate sample scraped data for testing/demo."""
    import json
    import random

    trades = ["Plumbing", "Electrical", "Carpentry", "Roofing", "HVAC", "Painting", "Landscaping", "Masonry"]
    cities = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ"]

    data = []
    for i in range(records):
        data.append({
            "business_name": f"{random.choice(['A-1', 'Best', 'Pro', 'Elite', 'AAA', 'Reliable'])} {random.choice(trades)} Services #{i+1}",
            "trade_category": random.choice(trades),
            "contact_name": f"Contact {i+1}",
            "email": f"info@business{i+1}.com",
            "phone": f"+1{random.randint(200,999)}{random.randint(100,999)}{random.randint(1000,9999)}",
            "city": random.choice(cities),
            "email_valid": True,
            "phone_valid": True,
        })

    from engine.exporter import export_csv, export_json, export_excel
    export_csv(data, "output/demo_output.csv")
    export_json(data, "output/demo_output.json")
    export_excel(data, "output/demo_output.xlsx")

    click.echo(f"✅ Generated {records} sample records → output/demo_output.csv / .json / .xlsx")


if __name__ == "__main__":
    cli()
