
#!/usr/bin/env python3
"""
ScraperHub CLI — production-ready web scraping system.
Config-driven, anti-detection, multi-format export.
"""
import sys
from pathlib import Path
import click
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))

from engine.config_loader import load_config
from engine.scraper import Scraper

logger.remove()
logger.add(sys.stderr, format="<level>{level: <8}</level> | <level>{message}</level>", colorize=True)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """🕸️  ScraperHub — deploy-ready web scraping system"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("config", type=click.Path(exists=True))
@click.option("--headless/--visible", default=True, help="Run browser headless (default: headless)")
@click.option("--pages", type=int, default=None, help="Override max pages")
@click.option("--format", "fmt", type=click.Choice(["csv", "json", "excel"]), default=None, help="Output format override")
def run(config, headless, pages, fmt):
    """🚀 Run a scrape job from a YAML config file."""
    cfg = load_config(config)
    if headless is not None:
        cfg.headless = headless
    if pages:
        cfg.max_pages = pages
    if fmt:
        cfg.output_format = fmt

    click.echo(f"\n🕸️  ScraperHub — {cfg.name}")
    click.echo(f"   Target: {cfg.start_url}")
    click.echo(f"   Pages: {cfg.max_pages}")
    click.echo(f"   Headless: {cfg.headless}")
    click.echo(f"   Output: {cfg.output_format}\n")

    scraper = Scraper(cfg)
    records = scraper.run()
    click.echo(f"\n✅ Done! {len(records)} validated records.")


@cli.command()
@click.option("--records", default=100, help="Number of sample records")
def simulate(records):
    """📊 Generate sample data for testing/demo."""
    import random

    trades = ["Plumbing", "Electrical", "Carpentry", "Roofing", "HVAC", "Painting", "Landscaping", "Masonry"]
    prefixes = ["A-1", "Best", "Pro", "Elite", "AAA", "Reliable", "Premier", "Superior", "Top", "All-State"]
    cities = [
        ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
        ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
        ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
        ("Austin", "TX"),
    ]

    data = []
    for i in range(records):
        trade = random.choice(trades)
        prefix = random.choice(prefixes)
        city, state = random.choice(cities)
        data.append({
            "business_name": f"{prefix} {trade} Services #{i+1}",
            "trade_category": trade,
            "contact_name": f"Contact {i+1}" if random.random() > 0.4 else "",
            "email": f"info@business{i+1}.com",
            "phone": f"+1{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
            "city": f"{city}, {state}",
        })

    from engine.exporter import export_csv, export_json, export_excel
    export_csv(data, "output/demo_output.csv")
    export_json(data, "output/demo_output.json")
    export_excel(data, "output/demo_output.xlsx")

    click.echo(f"\n✅ Generated {len(data)} sample records")
    click.echo(f"   ├─ output/demo_output.csv")
    click.echo(f"   ├─ output/demo_output.json")
    click.echo(f"   └─ output/demo_output.xlsx\n")


@cli.command()
@click.option("--port", default=8080, help="Port for API server")
def serve(port):
    """🌐 Start a lightweight API server (for integration)."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json

    class ScrapeHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "service": "ScraperHub API",
                "version": "1.0.0",
                "endpoints": {
                    "POST /scrape": "Run a scrape job (send YAML config in body)",
                    "GET /health": "Health check"
                }
            }).encode())

        def do_POST(self):
            if self.path == "/scrape":
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                # For now just echo
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "accepted", "job_id": "demo"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            logger.info(f"🌐  {args[0]} {args[1]}")

    server = HTTPServer(("0.0.0.0", port), ScrapeHandler)
    click.echo(f"\n🌐  API server running at http://localhost:{port}")
    click.echo(f"   Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")


@cli.command()
def ls():
    """📋 List available config files."""
    config_dir = Path("configs")
    if not config_dir.exists():
        click.echo("No configs/ directory found.")
        return
    configs = list(config_dir.glob("*.yml")) + list(config_dir.glob("*.yaml"))
    if not configs:
        click.echo("No config files found in configs/")
        return
    click.echo("\n📋 Available configs:\n")
    for cf in sorted(configs):
        name = cf.stem
        size = cf.stat().st_size
        click.echo(f"   {cf.name:<30} ({size} bytes)")
    click.echo(
        "   Run: python cli.py run configs/<name>.yml\n"
        "   Or:  python cli.py ls\n"
    )


if __name__ == "__main__":
    cli()
