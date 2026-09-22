from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from pathlib import Path

logs_dir = Path("./logs")
logs_dir.mkdir(parents=True, exist_ok=True)
dump_dir = Path("./dump")
dump_dir.mkdir(parents=True, exist_ok=True)


def pre_download_webdriver() -> None:
    """Trigger Selenium's internal manager to pre-download the Chrome WebDriver."""
    print("Pre-downloading the Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-web-security")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--force-device-scale-factor=1")

    print("Running webdriver...")
    service = Service(log_output=str(logs_dir / "pre_download_webdriver.log"))
    try:
        wd = webdriver.Chrome(options=options, service=service)
        wd.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 1920,
                "height": 1080,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )
        wd.get("https://www.google.com")
        wd.get_screenshot_as_file(
            str(dump_dir / "pre_download_webdriver_screenshot.png")
        )
    finally:
        wd.quit()

    print(f"Finished pre-downloading the webdriver: {service.path}")


if __name__ == "__main__":
    pre_download_webdriver()
