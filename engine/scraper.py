"""
Scraper orchestrator — ties browser, extractor, validator, and exporter together.
Features: retry, resume, live progress, stats summary.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from tqdm import tqdm

from engine.config_loader import TargetConfig
from engine.browser_manager import BrowserManager
from engine.extractor import Extractor
from engine.validator import DataValidator, deduplicate
from engine.exporter import EXPORTERS


class ScraperStats:
    def __init__(self):
        self.total_pages = 0
        self.pages_scraped = 0
        self.pages_failed = 0
        self.records_raw = 0
        self.records_valid = 0
        self.records_duplicates = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.errors: list[str] = []

    @property
    def elapsed(self) -> str:
        if not self.start_time:
            return "0s"
        end = self.end_time or time.time()
        secs = int(end - self.start_time)
        if secs < 60:
            return f"{secs}s"
        return f"{secs//60}m {secs%60}s"

    @property
    def rate(self) -> str:
        if not self.start_time:
            return "0/min"
        end = self.end_time or time.time()
        mins = (end - self.start_time) / 60
        if mins < 0.01:
            return f"{self.records_valid}/min"
        return f"{self.records_valid / mins:.0f}/min"

    def summary(self) -> str:
        return f"""
╔══════════════════════════════════════╗
║         Scrape Complete  ✅          ║
╠══════════════════════════════════════╣
║  Pages scraped    │ {self.pages_scraped:>4} / {self.total_pages:<4} ║
║  Pages failed     │ {self.pages_failed:>4}        ║
║  Raw records      │ {self.records_raw:>4}        ║
║  Duplicates rm'd  │ {self.records_duplicates:>4}        ║
║  Valid records    │ {self.records_valid:>4}  ✨      ║
║  Errors logged    │ {len(self.errors):>4}        ║
╠══════════════════════════════════════╣
║  Elapsed time     │ {self.elapsed:>10}   ║
║  Scrape rate      │ {self.rate:>10}   ║
╚══════════════════════════════════════╝"""


class Scraper:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.stats = ScraperStats()
        self.records: list[dict] = []
        self._checkpoint_path = Path("output") / f".checkpoint_{config.name.replace(' ', '_')}.json"

    def _save_checkpoint(self):
        """Save progress so we can resume if interrupted."""
        self._checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "records": self.records,
            "pages_done": self.stats.pages_scraped,
            "timestamp": datetime.now().isoformat(),
        }
        self._checkpoint_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_checkpoint(self) -> bool:
        """Load checkpoint from previous run. Returns True if resume happened."""
        if not self._checkpoint_path.exists():
            return False
        try:
            data = json.loads(self._checkpoint_path.read_text(encoding="utf-8"))
            self.records = data.get("records", [])
            resumed_pages = data.get("pages_done", 0)
            if self.records:
                logger.info(f"🔄 Resumed from checkpoint: {len(self.records)} records, {resumed_pages} pages done")
                self.stats.pages_scraped = resumed_pages
                self.stats.records_raw = len(self.records)
                return True
        except Exception:
            pass
        return False

    def scrape_listing_page(self, page, extractor: Extractor, pbar) -> int:
        """Scrape all item cards on the current listing page. Returns count."""
        from playwright.sync_api import TimeoutError as PwTimeout

        count = 0
        try:
            # Generic listing-card selectors
            card_selectors = [
                self.config.pagination or "",
                "[data-testid='search-result']",
                ".business-result",
                ".listing-card",
                ".result-item",
                ".business-card",
                "tr.item",
                "li.result",
                "[itemtype$='/Business']",
            ]
            if self.config.pagination:
                card_selectors = [self.config.pagination]

            cards = []
            for sel in card_selectors:
                if not sel:
                    continue
                try:
                    cards = page.query_selector_all(sel)
                    if cards:
                        break
                except Exception:
                    continue

            if not cards:
                logger.warning("⚠️  No listing cards found on page — selectors may need updating")
                return 0

            for card in cards:
                try:
                    record = extractor.extract_all()
                    if record.get("business_name") or record.get("email"):
                        record["source_url"] = page.url
                        self.records.append(record)
                        count += 1
                except Exception as e:
                    logger.warning(f"Card scrape error: {e}")

        except PwTimeout:
            logger.warning("Timeout scraping listing page")
        except Exception as e:
            logger.error(f"Listing page error: {e}")

        return count

    def run(self) -> list[dict]:
        """Main scrape loop with retry, resume, progress."""
        cfg = self.config
        self.stats.start_time = time.time()
        self.stats.total_pages = cfg.max_pages

        logger.info(f"🚀 Starting scrape: {cfg.name}")
        logger.info(f"🌐 Target URL: {cfg.start_url}")
        logger.info(f"📄 Pages: {cfg.max_pages} | Output: {cfg.output_format}")

        # Try resume
        resumed = self._load_checkpoint()

        bm = BrowserManager(
            headless=cfg.headless,
            proxy_list=cfg.proxy_list,
            human_delay=cfg.human_delay,
        )

        max_retries = 3
        retry_delay = 5

        try:
            browser = bm.start()
            page = bm.new_page()
            extractor = Extractor(page, cfg.fields)

            start_page = self.stats.pages_scraped + 1 if resumed else 1

            for page_num in range(start_page, cfg.max_pages + 1):
                retries = 0
                success = False

                while retries < max_retries and not success:
                    try:
                        if page_num == start_page and not resumed:
                            page.goto(cfg.start_url, wait_until="domcontentloaded", timeout=60000)
                        elif page_num > start_page:
                            # Try clicking next
                            next_btn = page.query_selector(
                                "a.next, .pagination .next, [rel=next], a:has-text('Next'), "
                                "a:has-text('next'), a:has-text('›'), a:has-text('»'), "
                                "button:has-text('Next'), button:has-text('next')"
                            )
                            if not next_btn:
                                logger.info("🔚 No more pages found.")
                                self.stats.pages_scraped = page_num - 1
                                success = True
                                break
                            next_btn.click()
                            page.wait_for_load_state("domcontentloaded")

                        bm.human_delay_s(page)
                        count = self.scrape_listing_page(page, extractor, None)
                        self.stats.records_raw += count
                        self.stats.pages_scraped = page_num
                        self.stats.pages_failed = 0

                        # Log progress with rate
                        elapsed = time.time() - self.stats.start_time
                        rate = count / (elapsed / 60) if elapsed > 0 else 0
                        logger.info(f"📄 Page {page_num}/{cfg.max_pages} → {count} records (total: {self.stats.records_raw}, {rate:.0f}/min)")

                        # Checkpoint every page
                        self._save_checkpoint()
                        success = True

                    except Exception as e:
                        retries += 1
                        logger.warning(f"⚠️  Page {page_num} attempt {retries}/{max_retries} failed: {e}")
                        if retries < max_retries:
                            time.sleep(retry_delay * retries)
                        else:
                            self.stats.pages_failed += 1
                            self.stats.errors.append(f"Page {page_num}: {str(e)}")
                            logger.error(f"❌ Page {page_num} failed after {max_retries} retries")

            # Validate & dedup
            validated = [DataValidator.validate_record(r) for r in self.records]
            before = len(validated)
            validated = deduplicate(validated)
            after = len(validated)

            self.stats.records_duplicates = before - after
            self.stats.records_valid = after

            # Export
            output_name = cfg.output_name or cfg.name.lower().replace(" ", "_")
            output_path = Path("output") / output_name
            fmt = cfg.output_format

            extensions = {"csv": ".csv", "json": ".json", "excel": ".xlsx"}
            if fmt in EXPORTERS:
                file_path = output_path.with_suffix(extensions[fmt])
                EXPORTERS[fmt](validated, file_path)
                logger.info(f"💾 Saved → {file_path}")

            # Also export summary as JSON
            summary_path = output_path.with_suffix(".summary.json")
            summary_data = {
                "project": cfg.name,
                "url": cfg.start_url,
                "scraped_at": datetime.now().isoformat(),
                "stats": {
                    "pages_scraped": self.stats.pages_scraped,
                    "pages_failed": self.stats.pages_failed,
                    "records_raw": self.stats.records_raw,
                    "records_valid": self.stats.records_valid,
                    "duplicates_removed": self.stats.records_duplicates,
                    "elapsed_seconds": int(time.time() - self.stats.start_time),
                },
                "fields": list(cfg.fields.keys()),
                "sample": validated[:3] if validated else [],
            }
            summary_path.write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding="utf-8")

            self.stats.end_time = time.time()
            print(self.stats.summary())

            # Clean up checkpoint on success
            if self._checkpoint_path.exists():
                self._checkpoint_path.unlink()

            return validated

        finally:
            bm.close()
