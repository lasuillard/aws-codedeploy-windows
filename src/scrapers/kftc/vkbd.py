from pathlib import Path
from typing import ClassVar

from statemachine import State
from structlog import get_logger
from structlog.stdlib import BoundLogger

from src.config import settings
from src.internal.vkbd import (
    BaseKeyboardMode,
    BaseKeymap,
    BaseVirtualKeyboard,
    DynamicMappingKey,
)

logger: BoundLogger = get_logger(__name__)


class Keymap(BaseKeymap):
    """Keymap for KFTCVAN."""

    img_dir = settings.assets_dir / "vkbd" / "kftc"
    dynamic_mapping: ClassVar = {
        DynamicMappingKey.Number: "NUMBER_{key}.png",
        DynamicMappingKey.AlphabetLower: "ALPHABET_SMALL_{key}.png",
        DynamicMappingKey.AlphabetUpper: "ALPHABET_LARGE_{key}.png",
        DynamicMappingKey.Special: "SPECIAL_{key}.png",
    }
    mapping: ClassVar = {
        "TOGGLE_SPECIAL_WHITE": "CONTROL_TOGGLE_SPECIAL (WHITE).png",
        "TOGGLE_SPECIAL_BLUE": "CONTROL_TOGGLE_SPECIAL (BLUE).png",
        "CONTROL_SHIFT_WHITE": "CONTROL_SHIFT (WHITE).png",
        "CONTROL_SHIFT_BLUE": "CONTROL_SHIFT (BLUE).png",
    }


class KeyboardMode(BaseKeyboardMode["VirtualKeyboard"]):
    """Keyboard state for KFTCVAN."""

    number_lower = State(initial=True)
    """Numbers and lowercased alphabets shown."""

    number_upper = State()
    """Numbers and uppercased alphabets shown."""

    special = State()
    """Special characters shown."""

    to_number = (
        number_lower.to(number_lower)
        | number_upper.to(number_upper)
        | special.to(number_lower)
    )
    to_lower = (
        number_lower.to(number_lower)
        | number_upper.to(number_lower)
        | special.to(number_lower)
    )
    to_upper = (
        number_lower.to(number_upper)
        | number_upper.to(number_upper)
        | special.to(number_upper)
    )
    to_special = (
        number_lower.to(special) | number_upper.to(special) | special.to(special)
    )

    @to_number.on
    @to_lower.on
    def _to_number_lower(self, event: str, source: State, target: State) -> None:
        if source == target:
            return

        if source == self.number_upper:
            self._vkbd.send_key("CONTROL_SHIFT_BLUE")
        elif source == self.special:
            self._vkbd.send_key("TOGGLE_SPECIAL_BLUE")
        else:
            logger.error("Unhandled transition: %s (%s -> %s)", event, source, target)

    @to_upper.on
    def _to_upper(self, event: str, source: State, target: State) -> None:
        if source == target:
            return

        if source == self.special:
            # No direct path to uppercase, go thorugh lowercase
            self._vkbd.send_key("TOGGLE_SPECIAL_BLUE")
            self._vkbd.send_key("CONTROL_SHIFT_WHITE")
        elif source == self.number_lower:
            self._vkbd.send_key("CONTROL_SHIFT_WHITE")
        else:
            logger.error("Unhandled transition: %s (%s -> %s)", event, source, target)

    @to_special.on
    def _to_special(self, event: str, source: State, target: State) -> None:
        if source == target:
            return

        self._vkbd.send_key("TOGGLE_SPECIAL_WHITE")


class VirtualKeyboard(BaseVirtualKeyboard[Keymap, KeyboardMode]):
    """Virtual keyboard for KFTCVAN login."""

    keymap_cls = Keymap
    mode_cls = KeyboardMode


# Save state diagram: `uv run python -m src.scrapers.kftc.vkbd`
if __name__ == "__main__":
    mode = KeyboardMode(vkbd=None)  # ty: ignore[invalid-argument-type]
    mode._graph().write_png(str(Path(__file__).parent / "mode.png"))
