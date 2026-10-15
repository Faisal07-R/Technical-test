"""
tests/test_pim.py
Scenario PIM -> Employee List OrangeHRM:
- TC-03 buka menu PIM -> halaman Employee List muncul, field input kosong
- TC-04 cari employee by name -> table menampilkan employee yang sesuai
- TC-05 delete employee via button delete di listing -> data hilang dari table
"""
import pytest

from pages.login_page import LoginPage
from pages.pim_employee_list_page import PIMEmployeeListPage
from pages.sidebar_page import SidebarPage


@pytest.mark.pim
def test_buka_pim_employee_list_field_kosong(page, base_url, test_data):
    # precondition: login dengan kredensial benar
    creds = test_data["credentials"]["valid"]
    login_page = LoginPage(page, base_url)
    login_page.navigate()
    login_page.login(creds["username"], creds["password"])
    login_page.expect_dashboard_visible()

    # Scenario: user masuk ke menu PIM
    sidebar = SidebarPage(page, base_url)
    sidebar.click_pim_menu()

    # Maka halaman Employee List muncul
    pim = PIMEmployeeListPage(page, base_url)
    pim.expect_page_loaded()

    # Dan semua field input dalam keadaan kosong / hanya menampilkan placeholder
    pim.expect_search_inputs_empty()


@pytest.mark.pim
def test_cari_employee_berdasarkan_nama_menampilkan_data_sesuai(page, base_url, test_data, employee_page):
    pim = employee_page
    pim.navigate()
    pim.expect_page_loaded()

    # Scenario: user mencari employee berdasarkan employee name
    # Ambil employee pertama yang ada di table agar test tidak bergantung
    # pada data bawaan demo yang bisa berubah sewaktu-waktu.
    name = pim.get_first_employee_name()
    assert name, "Table employee kosong; tidak ada data untuk diuji"
    pim.search_by_employee_name(name)

    # Maka table menampilkan employee yang namanya sesuai keyword pencarian
    names = pim.get_visible_employee_names()
    assert len(names) > 0, f"Pencarian {name!r} seharusnya menampilkan minimal satu employee"
    for employee_name in names:
        assert name.lower() in employee_name.lower(), (
            f"Employee {employee_name!r} tidak sesuai keyword pencarian {name!r}"
        )


@pytest.mark.pim
def test_hapus_employee_dari_table_data_hilang_dari_table(
    page, base_url, test_data, employee_page, ensure_employee_exists
):
    pim = employee_page
    pim.navigate()
    pim.expect_page_loaded()

    # precondition: pastikan ada employee yang akan dihapus
    employee = test_data["delete"]
    first = employee["employee_first_name"]
    last = employee["employee_last_name"]
    ensure_employee_exists(first, last, employee_id="7777")
    pim.navigate()
    pim.expect_search_inputs_empty()
    pim.expect_employee_in_table_after_search(first)

    # Scenario: user menghapus employee via button delete pada table listing
    modal = pim.delete_employee_by_name(first)
    pim.confirm_delete(modal)

    # Maka data employee tersebut tidak muncul lagi di table
    pim.expect_employee_name_not_in_table(first)
