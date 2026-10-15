
from playwright.sync_api import Locator, Page

from pages.base_page import BasePage, DEFAULT_TIMEOUT

LOGIN_PATH = "/web/index.php/auth/login"
DASHBOARD_PATH = "/web/index.php/dashboard/index"


class LoginPage(BasePage):
    @property
    def username_input(self) -> Locator:
        return self.page.locator('input[name="username"]')

    @property
    def password_input(self) -> Locator:
        return self.page.locator('input[name="password"]')

    @property
    def login_button(self) -> Locator:
        return self.page.locator('button[type="submit"]')

    @property
    def error_message(self) -> Locator:
        return self.page.locator(".oxd-alert-content-text")

    @property
    def error_alert(self) -> Locator:
        return self.page.get_by_role("alert")

    def navigate(self) -> None:
        """Buka halaman login OrangeHRM."""
        self.open(LOGIN_PATH)
        self.expect_visible(self.login_button)

    def fill_username(self, username: str) -> None:
        self.username_input.fill(username)

    def fill_password(self, password: str) -> None:
        self.password_input.fill(password)

    def click_login(self) -> None:
        self.login_button.click()

    def login(self, username: str, password: str) -> None:
        """Full flow login: isi + submit, tunggu dashboard atau error muncul.

        Pada aplikasi demo OrangeHRM, klik submit terkadang tidak memicu
        navigasi bila tombol belum siap (race condition dengan hydrasi React).
        Karena itu setelah klik kita polling hingga ada reaksi pasti: URL
        berubah ke dashboard ATAU alert error muncul.
        """
        self.fill_username(username)
        self.fill_password(password)
        self.click_login()
        self._wait_for_login_outcome()

    def _wait_for_login_outcome(self) -> None:
        """Tunggu hingga login jelas berhasil (URL dashboard) atau gagal (alert)."""
        self.page.wait_for_function(
            """() => {
                if (!window.location.href.includes('/auth/login')) return true;
                const el = document.querySelector('.oxd-alert-content-text');
                return !!el;
            }""",
            timeout=DEFAULT_TIMEOUT,
        )

    def expect_dashboard_visible(self) -> None:
        """Setelah login berhasil: URL dashboard dan header halaman muncul.

        Header dashboard ditemukan via role heading level 6 (locale-independent);
        app demo terkadang berbahasa lokal ("Cockpit" dll) sehingga
        pencocokan teks "Dashboard" tidak bisa diandalkan.
        """
        self.wait_for_url(DASHBOARD_PATH)
        self.expect_visible(self.page.get_by_role("heading", level=6).first)

    def expect_login_error_visible(self) -> None:
        """Setelah login gagal: alert error terlihat di halaman login."""
        self.expect_visible(self.error_message)

    def get_error_message_text(self) -> str:
        return self.error_message.inner_text().strip()

    def expect_still_on_login_page(self) -> None:
        """Login gagal: tetap di halaman login."""
        self.wait_for_url(LOGIN_PATH)
