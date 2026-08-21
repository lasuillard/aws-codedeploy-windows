class VirtualKeyboardError(Exception):
    """Top-level error for virtual keyboard."""


class MatchNotFoundError(VirtualKeyboardError):
    """Failed to find a match."""


class UnknownKeyError(VirtualKeyboardError):
    """Key is not known."""


class KeyImageLoadError(VirtualKeyboardError):
    """Failed to load key image."""


class StateDidNotChangedError(VirtualKeyboardError):
    """Exceeded retry limit watching state change."""
