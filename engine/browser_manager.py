"""
Browser manager — handles Playwright lifecycle, stealth, proxy rotation.
"""
import random
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page
from fake_useragent import UserAgent


class BrowserManager:
    def __init__(
        self,
        headless: bool = True,
        proxy_list: Optional[list[str]] = None,
        human_delay: tuple[float, float] = (0.5, 2.0),
    ):
        self.headless = headless
        self.proxy_list = proxy_list or []
        self._proxy_index = 0
        self._human_delay = human_delay
        self._browser: Optional[Browser] = None
        self._ua = UserAgent(browsers=["chrome", "edge", "firefox"])

    def _random_user_agent(self) -> str:
        return self._ua.random

    def _next_proxy(self) -> Optional[dict]:
        if not self.proxy_list:
            return None
        proxy_str = self.proxy_list[self._proxy_index % len(self.proxy_list)]
        self._proxy_index += 1
        parts = proxy_str.split("@")
        if len(parts) == 2:
            userpass, hostport = parts
            user, pwd = userpass.split(":")
            host, port = hostport.split(":")
            return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
        return {"server": f"http://{proxy_str}"}

    def start(self) -> Browser:
        launch_kwargs = {
            "headless": self.headless,
        }
        proxy = self._next_proxy()
        if proxy:
            launch_kwargs["proxy"] = proxy

        self._browser = sync_playwright().start().chromium.launch(**launch_kwargs)
        return self._browser

    def new_page(self) -> Page:
        assert self._browser, "Browser not started. Call .start() first."
        context = self._browser.new_context(
            user_agent=self._random_user_agent(),
            viewport={"width": random.randint(1200, 1920), "height": random.randint(800, 1080)},
            locale="en-US",
        )
        page = context.new_page()
        return page

    def human_delay_s(self, page: Page):
        """Wait a random amount of time to mimic human behaviour."""
        delay = random.uniform(*self._human_delay)
        page.wait_for_timeout(int(delay * 1000))

    def close(self):
        if self._browser:
            self._browser.close()
