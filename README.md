<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Status-Production-green" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Export-CSV%20%7C%20JSON%20%7C%20Excel-orange" alt="Export">
</p>

<h1 align="center">🕸️ ScraperHub</h1>
<p align="center"><b>Production-ready web scraping system</b><br>
Config-driven · Anti-detection · Proxy rotation · Resume from failures</p>

---

## ✨ Features

| Capability | Details |
|-----------|---------|
| 🛡️ **Anti-detection** | Playwright Stealth + real User-Agent rotation + random viewports + human-like delays |
| 🔄 **Proxy rotation** | Auto-rotate proxies per browser session |
| 🔁 **Auto retry** | 3x retry with exponential backoff on failures |
| 💾 **Resume support** | Saves checkpoint every page — resume if interrupted |
| 📊 **Live progress** | Real-time page count, record count, scrape rate |
| 📋 **Stats report** | Full summary: pages, records, duplicates, errors, elapsed time, rate |
| 📧 **Email validation** | Regex format check on every email field |
| 📞 **Phone validation** | Length/digit check + normalization |
| 🧹 **Deduplication** | Removes duplicates by business name, email, phone |
| 📁 **Multi-format export** | CSV, JSON, Excel (.xlsx) |
| ⚙️ **YAML config** | One config per target — no code changes needed |
| 🌐 **API server** | Optional REST API for integration with other systems |
| 🐳 **Docker support** | One-command deploy |

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt
playwright install chromium

# 2. Test with sample data
python cli.py simulate --records 100

# 3. Configure your target
#    Edit configs/template.yml with URL + CSS selectors

# 4. Run
python cli.py run configs/template.yml
```

---

## 📖 CLI Commands

```bash
# Run a scrape
python cli.py run configs/my_target.yml
python cli.py run configs/my_target.yml --visible    # Watch browser live
python cli.py run configs/my_target.yml --pages 10   # Override pages

# Generate sample data for testing
python cli.py simulate --records 500

# Start API server
python cli.py serve --port 8080

# List available configs
python cli.py list
```

---

## ⚙️ Configuration (YAML)

Edit a config file to point at any public directory website:

```yaml
name: "my_directory"
start_url: "https://example.com/directory"
max_pages: 5
fields:
  business_name: "h2.business-name"
  trade_category: ".category"
  email: "a[href^='mailto:']"
  phone: ".phone"
  city: ".location"
headless: true
human_delay: [0.5, 2.0]
output_format: "csv"
```

See `configs/template.yml` and `configs/yelp_example.yml` for full examples.

---

## 📊 Sample Output

```
╔══════════════════════════════════════╗
║         Scrape Complete  ✅          ║
╠══════════════════════════════════════╣
║  Pages scraped    │   25 /   25      ║
║  Pages failed     │    0            ║
║  Raw records      │  542           ║
║  Duplicates rm'd  │   23           ║
║  Valid records    │  519  ✨        ║
╠══════════════════════════════════════╣
║  Elapsed time     │   3m 12s       ║
║  Scrape rate      │  162/min       ║
╚══════════════════════════════════════╝
```

Output files:
- `output/my_project.csv` (or .json / .xlsx)
- `output/my_project.summary.json` — metadata + sample records

---

## 🐳 Docker

```bash
docker build -t scraper-hub .
docker run --rm scraper-hub simulate --records 100
docker run --rm -v $(pwd)/output:/app/output scraper-hub run configs/template.yml
```

---

## 🛠️ Tech Stack

**Python** · **Playwright** · **Pydantic** · **YAML** · **tqdm** · **loguru** · **openpyxl**

---

## 📄 License

MIT — free to use, modify, and deploy for client projects.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/hzzion2026">hzzion2026</a>
</p>
