from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def pre_download_webdriver() -> None:
    """Trigger Selenium's internal manager to pre-download the Chrome WebDriver."""
    print("Pre-downloading the Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    options.browser_version = "stable"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    print("Running webdriver...")
    service = Service(log_output="pre_download_webdriver.log")
    wd = webdriver.Chrome(options=options, service=service)
    try:
        wd.get("about:blank")
    finally:
        wd.quit()

    print("Finished pre-downloading the webdriver.")


if __name__ == "__main__":
    pre_download_webdriver()
