# ScraperHub 🕸️

**Deploy-ready web scraping system** — config-driven, anti-detection built-in, multi-format export.

## Features

- 🛡️ **Playwright Stealth** — evades bot detection
- 🔄 **Proxy rotation** — rotate IPs per browser launch
- 🧠 **Human-like behaviour** — random delays, real UA, variable viewports
- 📧 **Email/phone validation** — regex + format checks
- 🧹 **Deduplication** — remove duplicates by name, email, phone
- 📊 **Multi-format export** — CSV, JSON, Excel
- ⚙️ **YAML config** — one config per target, no code changes

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Run demo (generates sample data)
python cli.py simulate --records 100

# 3. Configure a target
# Edit configs/example.yml with the target URL and CSS selectors

# 4. Run
python cli.py run configs/example.yml
```

## Usage

```bash
python cli.py run configs/your_target.yml
python cli.py simulate --records 500
python cli.py demo
```

## Output

All output files go to `output/` directory.

## Sample Config

See `configs/example.yml` for a complete example.

## Tech Stack

Python · Playwright · Pydantic · YAML · openpyxl · loguru
