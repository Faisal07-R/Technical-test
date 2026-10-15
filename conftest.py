
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from pages.base_page import DEFAULT_TIMEOUT
from pages.login_page import LoginPage
from pages.pim_employee_list_page import PIMEmployeeListPage
from utils.data_loader import load_test_data

DEFAULT_BASE_URL = "https://opensource-demo.orangehrmlive.com"
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(ENV_FILE):
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)



def _find_chromium_executable() -> str | None:
    env_exe = os.getenv("CHROME_EXECUTABLE_PATH") or os.getenv("AGENT_BROWSER_EXECUTABLE_PATH")
    if env_exe and os.path.exists(env_exe):
        return env_exe

  
    candidates = [
        "/opt/data/cache/scratch/pw-browsers",
        
        os.path.expanduser("~/.cache/ms-playwright"),
        "/opt/hermes/.playwright",
        "/root/.cache/ms-playwright",
        "/opt/.cache/ms-playwright",
    ]
    for root in candidates:
        if not os.path.isdir(root):
            continue
        for entry in sorted(os.listdir(root)):
            folder = os.path.join(root, entry)
            if not os.path.isdir(folder):
                continue
            
            is_full = entry.startswith("chromium-") or entry == "chrome-linux64"
            is_shell = entry.startswith("chromium_headless_shell-")
            if not (is_full or is_shell):
                continue
            for name in ("chrome", "chrome-headless-shell", "headless_shell"):
                exe = os.path.join(folder, f"{name}-linux64", name)
                if os.path.exists(exe):
                    return exe
             
                exe = os.path.join(folder, name)
                if os.path.exists(exe):
                    return exe
                exe = os.path.join(folder, "chrome-linux", name)
                if os.path.exists(exe):
                    return exe

   
    for path in (
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/snap/bin/chromium",
    ):
        if os.path.exists(path):
            return path
    return None


CHROMIUM_EXECUTABLE = _find_chromium_executable()


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Tambah executable path Chromium bila browser Playwright belum diunduh."""
    if CHROMIUM_EXECUTABLE:
        return {
            **browser_type_launch_args,
            "executable_path": CHROMIUM_EXECUTABLE,
            "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        }
    return browser_type_launch_args


@pytest.fixture(scope="session")
def base_url() -> str:
    """URL root aplikasi OrangeHRM (dapat di-override via env BASE_URL)."""
    return os.getenv("BASE_URL", DEFAULT_BASE_URL).rstrip("/")


@pytest.fixture(scope="session")
def test_data() -> dict:
    """Test data dari tests/test_data.json (dipisah dari kode test)."""
    return load_test_data()


@pytest.fixture
def login_page(page, base_url) -> LoginPage:
    """Page object halaman login, sudah di-navigate ke URL login."""
    return LoginPage(page, base_url)


@pytest.fixture
def employee_page(page, base_url, test_data) -> PIMEmployeeListPage:
    """
    Page object PIM -> Employee List dalam keadaan SUDAH LOGIN.

    Dipakai oleh test PIM agar fokus pada scenario inti (tidak ulang login).
    """
    creds = test_data["credentials"]["valid"]
    login_page = LoginPage(page, base_url)
    login_page.navigate()
    login_page.login(creds["username"], creds["password"])
    login_page.expect_dashboard_visible()
    return PIMEmployeeListPage(page, base_url)


def _employee_created_marker(page) -> bool:
    
    return page.locator("div.oxd-toast--success").count() > 0


@pytest.fixture
def ensure_employee_exists(page, base_url):
    """
    Helper untuk test hapus employee.

    Membuat employee baru lewat PIM -> Add Employee bila belum ada, agar
    scenario delete selalu punya data yang valid dan unik. Demo OrangeHRM
    mereset data secara berkala, jadi kita tidak mengandalkan employee bawaan.

    Selector form pakai class OrangeHRM (orangehrm-firstname dst) karena
    placeholder label dilokalkan oleh demo (EN/DE/ES berubah-berulang).
    """
    def _ensure(first_name: str, last_name: str, employee_id: str = None) -> str:
        pim = PIMEmployeeListPage(page, base_url)
        employee_id = employee_id or "7777"
        pim.navigate()
        pim.search_by_employee_name(first_name)
        if pim.table_rows.count() > 0:
            return employee_id

        
        page.goto(
            base_url + "/web/index.php/pim/addEmployee",
            wait_until="domcontentloaded",
            timeout=DEFAULT_TIMEOUT,
        )
        page.wait_for_timeout(1000)
        page.locator("input.orangehrm-firstname").fill(first_name)
        page.locator("input.orangehrm-lastname").fill(last_name)
        id_input = page.locator(
            "input.oxd-input--active:not([class*='orangehrm-'])"
        ).first
        id_input.fill("")
        id_input.fill(employee_id)
        page.locator("form button[type='submit']").click()

        
        page.wait_for_function(
            "() => !!document.querySelector('div.oxd-toast--success')",
            timeout=DEFAULT_TIMEOUT,
        )
        page.wait_for_timeout(1000)
        return employee_id

    return _ensure
