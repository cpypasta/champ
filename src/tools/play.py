from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth #https://github.com/Mattwmaster58/playwright_stealth
from typing import Optional

def fetch(url: str) -> Optional[str]:
    try:
        with Stealth().use_sync(sync_playwright()) as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.evaluate("navigator.webdriver")
            context = browser.new_context()
            page = context.new_page()
            page.evaluate("navigator.webdriver")
            page.goto(url)
            html = page.content()
            browser.close()
            return html
    except Exception as ex:
        # print(ex)
        return None


if __name__ == "__main__":
    # fetch("https://www.semanticscholar.org/paper/84c8c874633fbb0aa1e48276fb31b1869d9b6766")   
    fetch("https://study.com/learn/lesson/growth-development-overview-examples.html") 