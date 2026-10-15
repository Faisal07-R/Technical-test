
import os
import re
from typing import Optional

from playwright.sync_api import Page, Locator, expect

# Timeout default untuk expect() - situs demo OrangeHRM seringkali lambat.
DEFAULT_TIMEOUT = 60_000


class BasePage:
    def __init__(self, page: Page, base_url: str = "") -> None:
        self.page = page
        self.base_url = base_url.rstrip("/") if base_url else ""

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def open(self, path: str = "") -> Page:
        """Navigasi ke path relatif terhadap base_url."""
        url = f"{self.base_url}{path}"
        self.page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
        # Setelah DOM ready, tunggu network idle agar konten dinamis selesai.
        try:
            self.page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)
        except Exception:
            # networkidle kadang tidak tercapai pada situs dengan polling;
            # bukan kegagalan test, lanjutkan dengan assertion polling.
            pass
        return self.page

    def current_path(self) -> str:
        """Path URL saat ini (tanpa host)."""
        return self.page.url.replace(self.base_url, "")

    def current_url(self) -> str:
        return self.page.url

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------
    def wait_for_url(self, path: str, timeout: Optional[int] = None) -> None:
        """Tunggu sampai URL mengandung `path` (substring, pakai regex)."""
        expect(self.page).to_have_url(
            re.compile(re.escape(path)), timeout=timeout or DEFAULT_TIMEOUT
        )

    def wait_for_heading(self, title: str, timeout: Optional[int] = None) -> None:
        """Tunggu sampai heading utama halaman terlihat."""
        expect(
            self.page.get_by_role("heading", name=title, exact=False)
        ).to_be_visible(timeout=timeout or DEFAULT_TIMEOUT)

    def wait_for_spinner_gone(self) -> None:
        """Tunggu sampai loading overlay OrangeHRM (jika ada) hilang."""
        spinner = self.page.locator("div.oxd-loading-spinner")
        try:
            spinner.wait_for(state="hidden", timeout=DEFAULT_TIMEOUT)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Assertion helpers
    # ------------------------------------------------------------------
    def expect_visible(self, locator: Locator, timeout: Optional[int] = None) -> None:
        expect(locator).to_be_visible(timeout=timeout or DEFAULT_TIMEOUT)

    def expect_hidden(self, locator: Locator, timeout: Optional[int] = None) -> None:
        expect(locator).to_be_hidden(timeout=timeout or DEFAULT_TIMEOUT)

    def expect_text_equals(self, locator: Locator, text: str, timeout: Optional[int] = None) -> None:
        expect(locator).to_have_text(text, timeout=timeout or DEFAULT_TIMEOUT)

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------
    def debug_screenshot(self, name: str = "debug") -> str:
        path = os.path.join("/tmp", f"orangehrm_{name}.png")
        self.page.screenshot(path=path)
        return path
