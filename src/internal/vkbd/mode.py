from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from statemachine import State, StateMachine
from structlog import get_logger
from structlog.stdlib import BoundLogger

if TYPE_CHECKING:
    from .keyboard import BaseVirtualKeyboard

logger: BoundLogger = get_logger(__name__)


class BaseKeyboardMode(StateMachine):
    """
    Base abstraction for virtual keyboard mode to manage available keymap.

    By default there is 4 state: lowercase (alphabet), uppercase, number and special,
    which most virtual keyboards do use them for password input.
    """

    def __init__(
        self,
        *args: Any,
        vkbd: "BaseVirtualKeyboard[Any, Any]",
        **kwargs: Any,
    ) -> None:
        """
        Initialize state machine with webdriver instance to delegate control.

        Args:
            args: Positional arguments passed to super.
            vkbd: Virtual keyboard instance.
            kwargs: Keyword arguments passed to super.

        """
        self._vkbd = vkbd
        super().__init__(*args, **kwargs)

    def before_transition(self, event: str, state: State) -> None:
        """Leave transition debug logs."""
        logger.debug("Handling event %s at state %s", event, state.id)

    # NOTE: Below transitions are mandatory as they are used in the virtual keyboard
    #       Also, no-op self-transition is required as well

    @abstractmethod
    def to_number(self) -> None:
        """Transition to number state."""

    @abstractmethod
    def to_lower(self) -> None:
        """Transition to lowercase state."""

    @abstractmethod
    def to_upper(self) -> None:
        """Transition to uppercase state."""

    @abstractmethod
    def to_special(self) -> None:
        """Transition to special state."""
