"""
Scraper orchestrator — ties browser, extractor, validator, and exporter together.
"""
import time
from pathlib import Path
from loguru import logger

from engine.config_loader import TargetConfig
from engine.browser_manager import BrowserManager
from engine.extractor import Extractor
from engine.validator import DataValidator, deduplicate
from engine.exporter import EXPORTERS


class Scraper:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.records: list[dict] = []
        self.errors: int = 0

    def scrape_listing_page(self, page, extractor: Extractor) -> int:
        """Scrape all item cards on the current listing page. Returns count."""
        from playwright.sync_api import TimeoutError as PwTimeout

        count = 0
        try:
            # Try common listing-card selectors
            card_selectors = [
                self.config.pagination or ".listing-card, .result-item, .business-card, tr.item, li.result",
            ]
            cards = []
            for sel in card_selectors:
                cards = page.query_selector_all(sel)
                if cards:
                    break

            for card in cards:
                try:
                    record = extractor.extract_all()
                    # Basic check: at least business_name should be present
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
        """Main scrape loop."""
        cfg = self.config
        logger.info(f"Starting scrape: {cfg.name}")
        logger.info(f"Target URL: {cfg.start_url}")

        bm = BrowserManager(
            headless=cfg.headless,
            proxy_list=cfg.proxy_list,
            human_delay=cfg.human_delay,
        )

        try:
            browser = bm.start()
            page = bm.new_page()
            extractor = Extractor(page, cfg.fields)

            page.goto(cfg.start_url, wait_until="domcontentloaded", timeout=60000)
            bm.human_delay_s(page)

            total = 0
            for page_num in range(1, cfg.max_pages + 1):
                logger.info(f"Page {page_num}/{cfg.max_pages}")
                count = self.scrape_listing_page(page, extractor)
                total += count
                logger.info(f"  → {count} records (total: {total})")

                # Try 'next page' pagination
                if page_num < cfg.max_pages:
                    next_btn = page.query_selector("a.next, .pagination .next, [rel=next], a:has-text('Next')")
                    if next_btn:
                        next_btn.click()
                        page.wait_for_load_state("domcontentloaded")
                        bm.human_delay_s(page)
                    else:
                        logger.info("No more pages found.")
                        break

            logger.info(f"Scraped {total} raw records")

            # Validate
            validated = [DataValidator.validate_record(r) for r in self.records]
            validated = deduplicate(validated)
            logger.info(f"After dedup: {len(validated)} records")

            # Export
            output_name = cfg.output_name or cfg.name.lower().replace(" ", "_")
            output_path = Path("output") / output_name
            fmt = cfg.output_format

            if fmt in EXPORTERS:
                file_path = output_path.with_suffix({ "csv": ".csv", "json": ".json", "excel": ".xlsx" }[fmt])
                EXPORTERS[fmt](validated, file_path)
                logger.info(f"Exported → {file_path}")

            return validated

        finally:
            bm.close()
