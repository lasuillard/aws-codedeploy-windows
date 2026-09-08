import re
import time
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self

from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium.webdriver import ChromeOptions, Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from structlog import get_logger

from src.config import settings
from src.internal.scraping import fetch
from src.scrapers.errors import (
    ContextNotInitializedError,
    InvalidCredentialsError,
    UnfulfilledRequirementError,
)

from .datamodels import KftcLoginCredential
from .vkbd import VirtualKeyboard

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

logger: BoundLogger = get_logger(__name__)


class KftcScraper:
    """KFTCVAN scraper."""

    name = "KFTCVAN"
    base_url = "https://kftcvan.or.kr"

    _dump_dir: Path
    _webdriver: Remote | None = None

    def __init__(self, *, dump_dir: Path | None = None) -> None:
        self._dump_dir = dump_dir or settings.dump_dir

    @property
    def webdriver(self) -> Remote:
        if self._webdriver is None:
            raise ContextNotInitializedError(
                "Webdriver instance is not initialized. Use KftcScraper as a context manager."
            )

        return self._webdriver

    def _get_webdriver(self) -> Remote:
        options = ChromeOptions()
        options.set_capability("platformName", "WINDOWS")

        # Disable "... wants to: Access other apps and services on this device" prompt
        # https://peter.sh/experiments/chromium-command-line-switches/#disable-web-security
        options.add_argument("--disable-web-security")

        self._webdriver = Remote(
            command_executor=settings.selenium_hub_url,
            options=options,
        )
        return self._webdriver

    def __enter__(self) -> Self:
        if self._webdriver is None:
            self._webdriver = self._get_webdriver()

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Any:
        if self._webdriver:
            if exc_type is not None:
                with suppress(Exception):
                    logger.warning(
                        "An error occurred during scraping, taking a screenshot for debugging."
                    )
                    self._webdriver.save_screenshot(
                        str(self._dump_dir / "error_screenshot.png")
                    )

            self._webdriver.quit()
            self._webdriver = None

        return False  # Re-raise the error

    # Login
    # ----------------------------------------------------------------------------------------------------------------
    def login(self, login_credential: KftcLoginCredential) -> None:
        """Login to KFTCVAN with provided user credential."""
        try:
            self._login(login_credential)
            self._validate_login(login_credential.username)
        except:
            logger.exception("Login failed")
            raise
        finally:
            self.webdriver.quit()

    def _login(self, login_credential: KftcLoginCredential) -> None:
        self.webdriver.maximize_window()
        self.webdriver.get(self.base_url + "/member/login/form.do")
        self._ensure_security_program_running()

        # ID is not protected by virtual keyboards
        id_input = self.webdriver.find_element(
            By.XPATH, "//input[@placeholder='아이디']"
        )
        WebDriverWait(self.webdriver, 10).until(EC.element_to_be_clickable(id_input))
        id_input.send_keys(login_credential.username)

        # Show virtual keyboard button
        pw_input = self.webdriver.find_element(By.ID, "passWd")
        vkbd_btn = self.webdriver.find_element(By.ID, "mobile-toggle")
        vkbd_btn.click()
        with suppress(NoAlertPresentException):
            alert = self.webdriver.switch_to.alert
            if (
                alert.text
                == """키보드보안 프로그램이 지원되지 않는 환경에서는
안전한 거래를 위해 가상키패드(마우스입력기)를
반드시 사용하셔야 합니다."""
            ):
                logger.debug("Site says keyboard security program isn't available.")
                alert.accept()
                pw_input.click()

        # Wait for virtual keyboard visible (not reliable)
        time.sleep(1)

        # Scroll down to the bottom of page to see whole virtual keyboard
        self.webdriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        vkbd = VirtualKeyboard(wd=self.webdriver, dump_dir=self._dump_dir)

        # Enter password
        def state_fn(webdriver: Remote) -> str:
            return pw_input.get_attribute("value")  # ty: ignore[invalid-return-type]

        vkbd.send_keys(login_credential.password.get_secret_value(), state_fn=state_fn)

        # Click login button
        login_btn = self.webdriver.find_element(By.CSS_SELECTOR, "a.btn_login")
        login_btn.click()

        # Wait for a while to see if any alert pops up, as it may indicate login failures
        with suppress(TimeoutException):
            logger.debug("Waiting for alert to see if login failed...")
            WebDriverWait(self.webdriver, 3).until(EC.alert_is_present())

        with suppress(NoAlertPresentException):
            logger.debug("Checking if alert is present to see if login failed...")
            alert_text = self.webdriver.switch_to.alert.text

            wrong_username_or_password = (
                alert_text == "ID 및 비밀번호를 다시 확인하시기 바랍니다."
            )
            wrong_password = (
                re.match(
                    r"비밀번호가 \d회 틀렸습니다. 5회 이상 오류입력시 로그인이 불가합니다.",
                    alert_text,
                )
                is not None
            )

            if wrong_username_or_password or wrong_password:
                logger.warning(
                    "Login failed because provided user credential is not valid: username=%s",
                    login_credential.username,
                )
                msg = "Login failed due to wrong user credentials."
                raise InvalidCredentialsError(msg)

    def _validate_login(self, username: str) -> bool:
        response = fetch(self.webdriver, url="/myPage.do", encoding="euc-kr")
        match = re.search(r'document.callCenter.CUST_ID.value ="(.+?)";', response.text)
        if not match:
            logger.warning("Failed to validate login, match not found")
            return False

        actual = match.group(1)
        if actual == username:
            logger.debug("Login validated")
            return True

        logger.warning(
            "Failed to validate login, match group is %r while expecting %r",
            actual,
            username,
        )
        return False

    def _ensure_security_program_running(self) -> None:
        """Security program may start late, so refresh the page a few times."""
        logger.debug("Checking for security program alert.")
        for retry in range(4):
            logger.debug("%d-th attempt to boot security program...", retry)
            try:
                alert = self.webdriver.switch_to.alert
            except NoAlertPresentException:
                break

            if alert.text not in (
                "보안프로그램을 설치하셔야 이용이 가능한 서비스입니다. [확인]을 선택하시면 설치페이지로 연결됩니다.",
                "인증서 관련 서비스를 지원하지 않는 환경입니다. 접속 가능 환경을 확인하시기 바랍니다.",
            ):
                logger.warning("Unexpected alert: %r", alert.text)
                break

            logger.debug(
                "Security program alert detected, dismissing alert and refreshing page."
            )
            alert.dismiss()
            self.webdriver.refresh()
        else:
            msg = "Security program may not running."
            raise UnfulfilledRequirementError(msg)
