from abc import ABC, abstractmethod
from typing import Any, Callable


class State(ABC):
    """
    Abstract base class for state machine states.

    States implement a three-phase lifecycle: setup, update, and exit. Each phase
    returns a boolean to allow conditional control flow. States are managed by
    StateMachine instances and can represent UI screens, game modes, menu systems,
    or any other discrete application state.

    State Transition Semantics:
        When transitioning from state A to state B via StateMachine.change():

        1. A.exit() is called first
           - If False is returned, the transition is aborted and A remains active
           - If True is returned, A has completed cleanup (handlers removed, etc.)

        2. B.setup() is called next
           - If False is returned, B declines to activate but A has already exited
           - If True is returned, the transition completes and B becomes active
           - If an exception is raised, A has already exited and cannot be restored

        Critical Consideration:
            If exit() returns True but setup() subsequently returns False, the state
            machine remains referencing the old state, but that state's exit() cleanup
            has already executed. This can result in a partially-deactivated state
            (e.g., event handlers removed but state still logically "active").

        Recommended Patterns:
            - Make exit() conditional: Only perform cleanup and return True if the
              transition is guaranteed to succeed
            - Make cleanup reversible: Store state in exit() that allows setup() to
              restore the previous state if needed
            - Design states to be idempotent: Ensure states can handle being in a
              post-exit condition gracefully

                Safe Transition Checklist:
                        1. Validate preconditions in setup() before expensive or irreversible work
                        2. Keep setup()/exit() side effects narrow and predictable
                        3. Perform state-local cleanup in exit() only when transition should proceed
                        4. Return False from exit() for recoverable conditions where transition
                             would break user interaction
                        5. Avoid relying on timing delays between exit() and setup(); use explicit
                             state transitions where possible

    Attributes:
        state_key: Identifier assigned by StateMachine when the state is registered
    """

    def __init__(self) -> None:
        self.state_key: str = ""

    @abstractmethod
    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Initialize the state when it becomes active.

        Called by the state machine when transitioning to this state. Implementers
        should perform initialization tasks such as registering event handlers,
        announcing UI elements via speech, or loading resources.

        Args:
            change_state: Callback to trigger state transitions (typically StateMachine.change)
            *args: Additional positional arguments passed from the transition call
            **kwargs: Additional keyword arguments passed from the transition call

        Returns:
            True if the state successfully initialized and should become active,
            False if the state declines to activate (note: previous state has already exited)
        """

    @abstractmethod
    def update(self, delta_time: float) -> bool:
        """
        Update the state's internal logic each frame.

        Called by the state machine on each frame while this state is active.
        Implementers should update animations, timers, or other per-frame logic.

        Args:
            delta_time: Time elapsed since the last update, in seconds

        Returns:
            True to continue running, False to signal application shutdown
        """

    @abstractmethod
    def exit(self) -> bool:
        """
        Clean up the state before transitioning away.

        Called by the state machine when attempting to transition to a different state.
        Implementers should perform cleanup such as removing event handlers, releasing
        resources, or saving data. This method executes before the new state's setup().

        Returns:
            True to allow the transition and confirm cleanup is complete,
            False to block the transition and remain in this state
        """
