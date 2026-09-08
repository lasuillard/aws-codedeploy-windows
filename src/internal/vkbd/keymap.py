import string
from abc import ABC
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import cv2
from cv2.typing import MatLike
from structlog import get_logger

from .errors import KeyImageLoadError, UnknownKeyError

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

logger: BoundLogger = get_logger(__name__)


class DynamicMappingKey(StrEnum):
    """Enum for dynamic key mapping."""

    Number = "__number__"
    AlphabetLower = "__alphabet_lower__"
    AlphabetUpper = "__alphabet_upper__"
    Special = "__special__"


class BaseKeymap(ABC):
    """
    Key mapping for virtual keyboards.

    There are lots of keys in keyboard and it's hard to remember all of them.
    This class provides a mapping of keyboard keys to their corresponding images.

    It is recommended to use predefined naming format for key images to reduce config overhead.
    """

    special_characters: ClassVar[dict[str, str]] = {
        "&": "AMPERSAND",
        "'": "APOSTROPHE",
        "*": "ASTERISK",
        "@": "AT",
        "\\": "BACKSLASH",
        "`": "BACK_QUOTE",
        "^": "CARET",
        ":": "COLON",
        ",": "COMMA",
        "$": "DOLLAR",
        "=": "EQUAL",
        "!": "EXCLAMATION_POINT",
        ">": "GREATER_THAN",
        "#": "HASH",
        "-": "HYPHEN",
        "{": "LEFT_BRACE",
        "[": "LEFT_BRACKET",
        "(": "LEFT_PARENTHESIS",
        "<": "LESS_THAN",
        "%": "PERCENT",
        ".": "PERIOD",
        "+": "PLUS",
        "?": "QUESTION_MARK",
        '"': "QUOTATION_MARK",
        "}": "RIGHT_BRACE",
        "]": "RIGHT_BRACKET",
        ")": "RIGHT_PARENTHESIS",
        ";": "SEMICOLON",
        "/": "SLASH",
        "~": "TILDE",
        "_": "UNDERSCORE",
        "|": "VERTICAL_BAR",
    }
    """Mapping of special characters to their names."""

    dynamic_mapping: ClassVar[dict[DynamicMappingKey, str]]
    """Map of dynamic key to name of file in image directory."""

    mapping: ClassVar[dict[str, str]]
    """Map of keyboard key to name of file in image directory.

    Static mapping takes precedence over dynamic mapping.
    """

    img_dir: Path
    """Directory holding key image files."""

    _map_img: dict[str, MatLike]
    """Map of key to loaded image."""

    def __init__(self) -> None:
        """Initialize keymap, loading images to memory."""
        key_to_filename = {}

        # Dynamic mapping
        for key in string.digits:
            filename = self.dynamic_mapping[DynamicMappingKey.Number].format(key=key)
            key_to_filename[key] = filename

        for key in string.ascii_lowercase:
            filename = self.dynamic_mapping[DynamicMappingKey.AlphabetLower].format(
                key=key
            )
            key_to_filename[key] = filename

        for key in string.ascii_uppercase:
            filename = self.dynamic_mapping[DynamicMappingKey.AlphabetUpper].format(
                key=key
            )
            key_to_filename[key] = filename

        for key in string.punctuation:
            translated = self.special_characters.get(key, None)
            if not translated:
                logger.warning("Special character %s is not mapped to a name.", key)
                continue

            filename = self.dynamic_mapping[DynamicMappingKey.Special].format(
                key=translated
            )
            key_to_filename[key] = filename

        # Apply static mapping
        for key, filename in self.mapping.items():
            key_to_filename[key] = filename

        # Load images
        map_img = {
            k: cv2.imread(str(self.img_dir / v)) for k, v in key_to_filename.items()
        }
        load_failed = ", ".join(k for k, kf in map_img.items() if kf is None)
        if load_failed:
            msg = f"{len(load_failed)} key images failed to load: {load_failed}"
            raise KeyImageLoadError(msg)

        self._map_img = map_img  # ty: ignore[invalid-assignment]

    def get(self, key: str) -> MatLike:
        """Return matching image for key."""
        img = self._map_img.get(key, None)
        if img is None:
            msg = f"Key {key} is not in keymap."
            raise UnknownKeyError(msg)

        return img
