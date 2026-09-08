"""
Browser virtual keyboard controller.

References
----------
- https://gist.github.com/datakurre/65ccd79b78268d4592f5530f014b61e2
- https://github.com/soulee-dev/fuckvkeypad

"""

import string
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from structlog import get_logger

from .errors import MatchNotFoundError, StateDidNotChangedError
from .keymap import BaseKeymap
from .mode import BaseKeyboardMode

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from cv2.typing import MatLike
    from selenium.webdriver.remote.webdriver import WebDriver
    from structlog.stdlib import BoundLogger

logger: BoundLogger = get_logger(__name__)


class BaseVirtualKeyboard[KM: BaseKeymap, KS: BaseKeyboardMode](ABC):
    """Virtual keyboard abstract base class."""

    @property
    @abstractmethod
    def keymap_cls(self) -> type[KM]:
        """Keymap class for virtual keyboard."""

    @property
    @abstractmethod
    def mode_cls(self) -> type[KS]:
        """Keyboard mode class type."""

    def __init__(self, *, wd: WebDriver, dump_dir: Path) -> None:
        """
        Initialize virtual keyboard.

        Args:
            wd: Webdriver instance.
            dump_dir: Directory to store dump files for debugging.

        """
        self._wd = wd
        self._keymap = self.keymap_cls()
        self._mode = self.mode_cls(vkbd=self)
        self._dump_dir = dump_dir

    def send_keys(
        self,
        keys: str | Iterable[str],
        *,
        state_fn: Callable[[WebDriver], Any],
        watch_interval: float = 0.05,
        retry: int = 10,  # 5 seconds by default
    ) -> None:
        """
        Send multiple keys.

        Args:
            keys: Keys to stroke.
            state_fn: Callable that returns state. Next key stroke only will be made if state changes.
                If state bases on sensitive inputs, consider using hash functions.
            watch_interval: Interval to check state changes.
            retry: Retry limit of wait for changes. If exceeded, `TimeoutError` will be raised.

        Raises:
            MaxRetryExceededError: State did not change for given `timeout`.

        """
        for key in keys:
            current_state = state_fn(self._wd)

            logger.debug("Sending key %r, current state is %r", key, current_state)
            self.ensure_mode(key)
            self.send_key(key)

            for i in range(retry):
                logger.debug("Waiting for state change: %d-th try", i)
                time.sleep(watch_interval)

                new_state = state_fn(self._wd)
                if current_state != new_state:
                    logger.debug(
                        "State changed from %r to %r; escaping loop",
                        current_state,
                        new_state,
                    )
                    break

                logger.debug("State did not change.")
            else:
                msg = f"State did not change for {retry} retries."
                raise StateDidNotChangedError(msg)

    def ensure_mode(self, key: str) -> None:
        """
        Ensure given key is clickable by transitioning to appropriate state.

        Args:
            key: Key to stroke.

        """
        if key in string.ascii_lowercase:
            self._mode.to_lower()
        elif key in string.ascii_uppercase:
            self._mode.to_upper()
        elif key in string.digits:
            self._mode.to_number()
        elif key in string.punctuation:
            self._mode.to_special()

        # NOTE: `else` not handled as error as there are control keys

    def send_key(self, key: str, *, threshold: float | None = None) -> None:
        """
        Send a single key.

        Args:
            key: Key to storke.
            threshold: Match threshold. Defaults to `None`.

        """
        screen = self._get_screen()
        x, y = self._locate_key(screen, key=key, threshold=threshold, draw_area=True)
        self._click_element_at(x=x, y=y, img=screen, draw_point=True)
        self._write_img(screen)

    def _locate_key(
        self,
        img: MatLike,
        *,
        key: str,
        threshold: float | None = None,
        draw_area: bool = False,
    ) -> tuple[int, int]:
        """
        Find key from given image.

        Args:
            img: Image to to search key for.
            key: Key to find image from.
            threshold: Match threshold to raise error. If `None`, do not raise.
            draw_area: Draw matching area to given image. Defaults to `False`.

        Raises:
            MatchNotFoundError: Matching image not found for given `threshold`.
                If `threshold` is not set, it will not raised.

        Returns:
            Center position of match area.

        """
        key_img = self._keymap.get(key)
        w, h = key_img.shape[1], key_img.shape[0]

        # Find match
        match = cv2.matchTemplate(img, key_img, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(match)
        x, y = max_loc[0], max_loc[1]

        # Draw blue rectangle for match area
        if draw_area:
            cv2.rectangle(img, max_loc, (x + w, y + h), (255, 0, 0), thickness=3)

        # Assert threshold
        if threshold and max_val >= threshold:
            msg = f"Failed to find a match; max: {max_val}"
            raise MatchNotFoundError(msg)

        return (int(x + w / 2), int(y + h / 2))

    def _click_element_at(
        self,
        *,
        x: int,
        y: int,
        draw_point: bool = False,
        img: MatLike | None = None,
    ) -> None:
        """
        Click element at position.

        Args:
            x: Point x.
            y: Point y.
            draw_point: _description_. Defaults to `False`.
            img: Image to draw point. Required if `draw_point` is `True`.
                Image is not used for clicking; it's just for drawing point.

        """
        elem = self._wd.execute_script(f"return document.elementFromPoint({x}, {y});")
        if not isinstance(elem, WebElement):
            logger.warning(
                "Element at point is not `WebElement` instance, actual: %s", type(elem)
            )

        # Leave a dot (filled red circle) at click position
        if draw_point:
            if img is None:
                msg = "Image is required to draw point."
                raise ValueError(msg)

            cv2.circle(img, (x, y), radius=7, color=(0, 0, 255), thickness=-1)

        actions = ActionChains(self._wd)
        actions.move_to_element(elem).click().perform()

    def _get_screen(self) -> MatLike:
        """Get current webdriver screenshot."""
        png = self._wd.get_screenshot_as_png()
        data = np.asarray(bytearray(png), dtype=np.uint8)

        return cv2.imdecode(data, cv2.IMREAD_COLOR)  # ty: ignore[invalid-return-type]

    def _write_img(self, img: MatLike) -> None:
        """Shortcut write image to temporary file."""
        file = self._dump_dir / f"{datetime.now(UTC):%Y%m%d_%H%M%S%f}.png"
        cv2.imwrite(str(file), img)
