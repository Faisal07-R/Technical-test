
from playwright.sync_api import Locator, Page

from pages.base_page import BasePage

# path modul OrangeHRM (locale-independent)
PIM_MODULE_PATH = "/web/index.php/pim/viewPimModule"


class SidebarPage(BasePage):
    @property
    def nav_links(self) -> Locator:
        return self.page.locator("aside.oxd-sidepanel li.oxd-main-menu-item-wrapper a")

    def menu(self, name: str) -> Locator:
        """Locator menu sidebar berdasarkan teks (mis. "PIM")."""
        return self.page.locator(
            "aside.oxd-sidepanel li.oxd-main-menu-item-wrapper a", has_text=name
        )

    def menu_by_href(self, path: str) -> Locator:
        """Locator menu sidebar berdasarkan href modul (locale-independent)."""
        return self.page.locator(
            "aside.oxd-sidepanel li.oxd-main-menu-item-wrapper "
            f'a[href="{path}"]'
        )

    def click_menu(self, name: str) -> None:
        self.menu(name).first.click()
        self.wait_for_spinner_gone()

    def click_pim_menu(self) -> None:
        """Klik menu PIM secara locale-independent (via href modul)."""
        self.menu_by_href(PIM_MODULE_PATH).first.click()
        self.wait_for_spinner_gone()

    def expect_menu_visible(self, name: str) -> None:
        self.expect_visible(self.menu(name))
