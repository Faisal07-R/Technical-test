"""
tests/test_login.py
Scenario login OrangeHRM:
- TC-01 login dengan kredensial benar -> masuk dashboard
- TC-02 login dengan kredensial salah -> pesan error "Invalid credentials"
"""
import pytest

from pages.login_page import LoginPage


@pytest.mark.login
def test_login_dengan_kredensial_benar_masuk_dashboard(login_page: LoginPage, test_data):
    # Scenario: user login dengan kredensial yang benar
    creds = test_data["credentials"]["valid"]
    login_page.navigate()
    login_page.login(creds["username"], creds["password"])

    # Maka user masuk ke halaman dashboard
    login_page.expect_dashboard_visible()
    assert "dashboard" in login_page.current_path(), (
        f"URL seharusnya mengandung /dashboard/, actual: {login_page.current_url()}"
    )


@pytest.mark.login
def test_login_dengan_kredensial_salah_menampilkan_error(login_page: LoginPage, test_data):
    # Scenario: user login dengan kredensial yang salah
    creds = test_data["credentials"]["invalid"]
    login_page.navigate()
    login_page.login(creds["username"], creds["password"])

    # Maka muncul pesan error dan user tetap di halaman login
    login_page.expect_login_error_visible()
    error_text = login_page.get_error_message_text()
    assert "invalid credentials" in error_text.lower(), (
        f"Pesan error seharusnya berisi 'Invalid credentials', actual: {error_text!r}"
    )
    login_page.expect_still_on_login_page()
