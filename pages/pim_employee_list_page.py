
from playwright.sync_api import Locator, Page

from pages.base_page import BasePage, DEFAULT_TIMEOUT
from pages.common_modal import ConfirmModal

PIM_EMPLOYEE_LIST_PATH = "/web/index.php/pim/viewEmployeeList"

FILTER_FORM = "div.oxd-table-filter"


class PIMEmployeeListPage(BasePage):
    @property
    def header(self) -> Locator:
        """Header h5 halaman Employee List (locale-independent)."""
        return self.page.locator("div.orangehrm-background-container h5").first

    @property
    def employee_name_input(self) -> Locator:
        """Input Employee Name pada filter bar (hint input pertama)."""
        return self.page.locator(
            f"{FILTER_FORM} input[placeholder='Type for hints...']"
        ).first

    @property
    def employee_id_input(self) -> Locator:
        """Input Employee Id pada filter bar."""
        return self.page.locator(f"{FILTER_FORM} input.oxd-input--active").first

    @property
    def search_button(self) -> Locator:
        """Tombol Search: tombol terakhir di filter bar (locale-independent)."""
        return self.page.locator(f"{FILTER_FORM} button").last

    @property
    def reset_button(self) -> Locator:
        """Tombol Reset: tombol kedua dari belakang di filter bar (locale-independent)."""
        return self.page.locator(f"{FILTER_FORM} button").nth(-2)

    @property
    def table(self) -> Locator:
        return self.page.locator("div.oxd-table.orangehrm-employee-list")

    @property
    def table_body(self) -> Locator:
        return self.page.locator("div.oxd-table-body").first

    @property
    def table_rows(self) -> Locator:
        """Seluruh baris data employee (tidak termasuk header)."""
        return self.table_body.locator("div.oxd-table-card")

    @property
    def no_records_message(self) -> Locator:
        """Pesan 'data tidak ditemukan' (locale-independent: table body kosong)."""
        return self.table_body

    # ------------------------------------------------------------------
    # Navigasi & state
    # ------------------------------------------------------------------
    def navigate(self) -> None:
        self.open(PIM_EMPLOYEE_LIST_PATH)
        self.expect_page_loaded()

    def expect_page_loaded(self) -> None:
        """Halaman Employee List termuat: header terlihat dan table ada."""
        self.expect_visible(self.header)
        self.expect_visible(self.table_body)
        self.wait_for_spinner_gone()

    # ------------------------------------------------------------------
    # Pencarian
    # ------------------------------------------------------------------
    def search_by_employee_name(self, name: str) -> None:
        self.employee_name_input.fill(name)
        # Tutup autocomplete dropdown yang mungkin menutupi tombol Search.
        self.page.keyboard.press("Escape")
        self.search_button.click()
        self.wait_for_spinner_gone()
        # Tunggu hingga table selesai dimuat ulang. Pada demo OrangeHRM
        # pencarian tanpa hasil membuat table body kosong total (tidak ada
        # pesan "No Records Found" yang reliable), jadi kondisi selesai
        # cukup mendeteksi: spinner hilang + jumlah baris stabil.
        self._wait_for_table_settled()

    def _wait_for_table_settled(self, stable_ticks: int = 2, max_ms: int = 30000) -> None:
        """Tunggu hingga jumlah baris table tidak berubah selama N poll berturut-turut."""
        import time

        deadline = time.monotonic() + max_ms / 1000.0
        last = -1
        stable = 0
        while time.monotonic() < deadline:
            current = self.table_rows.count()
            if current == last:
                stable += 1
                if stable >= stable_ticks:
                    return
            else:
                stable = 0
                last = current
            self.page.wait_for_timeout(500)
        return  # fallback: anggap settled setelah timeout

    def reset_filter(self) -> None:
        self.reset_button.click()
        self.wait_for_spinner_gone()

    # ------------------------------------------------------------------
    # Penghapusan employee
    # ------------------------------------------------------------------
    def delete_icon_in_row(self, index: int) -> Locator:
        return self.table_rows.nth(index).locator("button i.bi-trash").first

    def delete_row_by_index(self, index: int) -> ConfirmModal:
        """Klik ikon delete pada baris ke-index (0-based), kembalikan modal konfirmasi."""
        self.delete_icon_in_row(index).click()
        return ConfirmModal(self.page, self.base_url)

    def delete_employee_by_name(self, name: str) -> ConfirmModal:
        """Cari employee berdasarkan nama lalu hapus baris pertama yang cocok."""
        self.search_by_employee_name(name)
        self.delete_row_by_index(0)
        return ConfirmModal(self.page, self.base_url)

    def confirm_delete(self, modal: ConfirmModal) -> None:
        modal.expect_dialog_visible()
        modal.confirm()
        self.expect_toast_success_visible()

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------
    def expect_toast_success_visible(self) -> None:
        self.expect_visible(self.page.locator("div.oxd-toast--success"))

    def get_visible_employee_names(self) -> list:
        """Nama depan + tengah seluruh employee yang sedang tampil di table."""
        if self.table_rows.count() == 0:
            return []
        return [
            r.inner_text().strip()
            for r in self.table_rows.locator("div.oxd-table-cell:nth-child(3)").all()
        ]

    def get_first_employee_name(self) -> str:
        """Nama employee pada baris pertama table (dipakai untuk pencarian dinamis)."""
        if self.table_rows.count() == 0:
            return ""
        return self.table_rows.first.locator(
            "div.oxd-table-cell:nth-child(3)"
        ).inner_text().strip()

    def expect_no_rows(self) -> None:
        """Table tidak menampilkan baris employee (body kosong)."""
        assert self.table_rows.count() == 0, "Seharusnya tidak ada baris employee"

    def expect_employee_in_table(self, name: str) -> None:
        names = self.get_visible_employee_names()
        assert name in names, f"Employee {name!r} tidak ditemukan di table: {names}"

    def expect_employee_name_not_in_table(self, name: str) -> None:
        names = self.get_visible_employee_names()
        assert name not in names, (
            f"Employee {name!r} seharusnya sudah terhapus, tetapi masih ada di table: {names}"
        )

    def expect_search_inputs_empty(self) -> None:
        """Semua field input pencarian kosong atau hanya menampilkan placeholder."""
        inputs = self.page.locator(f"{FILTER_FORM} input").all()
        assert len(inputs) > 0, "Tidak ada field input filter yang ditemukan"
        for i, inp in enumerate(inputs):
            value = inp.input_value()
            placeholder = inp.get_attribute("placeholder")
            assert value == "", (
                f"Input filter ke-{i} (placeholder={placeholder!r}) tidak kosong: value={value!r}"
            )

    def expect_employee_in_table_after_search(self, name: str) -> None:
        """Cari employee lalu pastikan ia muncul di table (sebagai precondition test)."""
        self.search_by_employee_name(name)
        rows = self.table_rows.count()
        assert rows > 0, f"Precondition gagal: employee {name!r} tidak ditemukan di table"
