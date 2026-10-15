
from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class ConfirmModal(BasePage):
    @property
    def dialog(self) -> Locator:
        return self.page.locator("div.oxd-dialog-sheet")

    @property
    def confirm_button(self) -> Locator:
        return self.dialog.locator("button.oxd-button--label-danger")

    @property
    def cancel_button(self) -> Locator:
        return self.dialog.locator("button.oxd-button--ghost")

    def expect_dialog_visible(self) -> None:
        """Dialog konfirmasi terlihat di layar."""
        self.expect_visible(self.dialog)

    def confirm(self) -> None:
        self.confirm_button.click()

    def cancel(self) -> None:
        self.cancel_button.click()
