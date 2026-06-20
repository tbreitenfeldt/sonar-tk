from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    cast,
)

import pyglet
from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.ui.element.text_label import TextLabel
from sonartk.util.state import State
from sonartk.util.state_machine import StateMachine

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen


class Menu(Element[str]):
    def __init__(
        self,
        parent: Screen,
        label: str = "",
        items: List[Dict[str, Element | str]] | None = None,
        position: int = 0,
        has_border: bool = False,
        is_first_letter_navigation: bool = True,
        is_side_menu: bool = False,
        reset_position_on_focus: bool = True,
    ) -> None:
        # Set attributes before calling super().__init__() since bind_keys() needs them
        self.has_border: bool = has_border
        self.is_first_letter_navigation: bool = is_first_letter_navigation
        self.is_side_menu: bool = is_side_menu
        self.reset_position_on_focus: bool = reset_position_on_focus
        self.position: int = position
        self.default_position: int = position
        self.typing_buffer: str = ""
        self.state_machine: StateMachine = StateMachine()
        self.state_machine.set_current_index(position)

        super().__init__(parent=parent, label=label, value="", role="menu")  # type: ignore

        if items:
            for item in items:
                if not item or len(item) > 1:
                    raise ValueError("Requires 1 dictionary entry.")
                else:
                    k, v = next(iter(item.items()))
                    self.add(k, v)

    # override
    def bind_keys(self) -> None:
        """Bind keyboard controls for navigation, submission, and text lookup."""
        if self.is_side_menu:
            self.key_handler.add_key_press(self.next_item, key.RIGHT)
            self.key_handler.add_key_press(self.previous_item, key.LEFT)
        else:
            self.key_handler.add_key_press(self.next_item, key.DOWN)
            self.key_handler.add_key_press(self.previous_item, key.UP)

        self.key_handler.add_key_press(self.navigate_to_beginning, key.HOME)
        self.key_handler.add_key_press(self.navigate_to_end, key.END)
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

        if self.is_first_letter_navigation:
            self.key_handler.add_on_text_input(self.navigate_by_first_letter)

    # override
    @property
    def value(self) -> Optional[str]:
        """Return the key of the currently selected menu item."""
        return list(self.state_machine.states)[self.position]

    # override
    @value.setter
    def value(self, value: str) -> None:
        """Return the key of the currently selected menu item."""
        index: int = 0
        for k in self.state_machine.states.keys():
            if k == value:
                break
            index += 1

        self.position = index
        self.state_machine.set_current_index(index)
        self.state_machine.transition_to(value)

    # override
    def setup(  # type: ignore[override]
        self,
        change_state: Callable[[str, Any], None],
        interrupt_speech: bool = True,
    ) -> bool:
        """Prepare menu focus state and activate the current item."""
        super().setup(change_state, interrupt_speech)

        if self.reset_position_on_focus:
            self.position = self.default_position
            self.state_machine.set_current_index(self.position)

        self.activate_current_state(interrupt_speech=False)
        return True

    # override
    def update(self, delta_time: float) -> bool:
        """Update both the base element and the active menu item state."""
        super().update(delta_time)
        return self.state_machine.update(delta_time)

    # override
    def exit(self) -> bool:
        """Exit the active menu item and then exit this menu element."""
        return self.state_machine.current_state.exit() and super().exit()

    def _navigate_item(self, delta: int) -> bool:
        """
        Navigate to next/previous item with border handling.

        Args:
            delta: Direction to navigate (1 for next, -1 for previous)
        """
        if not self.has_border:
            self.dispatch_event("on_change", self)
            self.position = (self.position + delta) % self.state_machine.size()
            self.activate_current_state()
        else:
            new_position = self.position + delta
            if self.state_machine.size() == 1:
                self.dispatch_event("on_border", self)
                self.activate_current_state()
            elif 0 <= new_position < self.state_machine.size():
                self.dispatch_event("on_change", self)
                self.position = new_position
                self.activate_current_state()
            else:
                self.dispatch_event("on_border", self)

        return True

    def next_item(self) -> bool:
        """Move to the next menu item, honoring border behavior."""
        return self._navigate_item(1)

    def previous_item(self) -> bool:
        """Move to the previous menu item, honoring border behavior."""
        return self._navigate_item(-1)

    def navigate_to_beginning(self) -> bool:
        """Jump focus to the first menu item."""
        if self.position != 0:
            self.dispatch_event("on_change", self)
            self.position = 0
            self.activate_current_state()

        return True

    def navigate_to_end(self) -> bool:
        """Jump focus to the last menu item."""
        if self.position != self.state_machine.size() - 1:
            self.dispatch_event("on_change", self)
            self.position = self.state_machine.size() - 1
            self.activate_current_state()

        return True

    def submit(self) -> bool:
        """Emit the submit event for the currently selected item."""
        self.dispatch_event("on_submit", self)
        return True

    def navigate_by_first_letter(self, character: str) -> bool:
        """Navigate by typed text with immediate response and timed refinement.

        First character:
            Jump immediately to the next matching item after the current
            position, wrapping to the top if needed.
        Repeated same character:
            Cycle through items that start with that character.
        Additional characters before timeout:
            Refine search from the beginning using the full prefix.
        """
        pyglet.clock.unschedule(self._clear_typing_buffer)

        if (
            self.typing_buffer
            and character.lower() == self.typing_buffer[0].lower()
            and all(
                c.lower() == self.typing_buffer[0].lower()
                for c in self.typing_buffer
            )
        ):
            self.typing_buffer = character
            self._navigate_by_prefix(start=self.position + 1, wrap=True)
        else:
            is_first_character = self.typing_buffer == ""
            self.typing_buffer += character

            if is_first_character:
                self._navigate_by_prefix(start=self.position + 1, wrap=True)
            else:
                self._navigate_by_prefix(start=0, wrap=False)

        pyglet.clock.schedule_once(self._clear_typing_buffer, 0.4)
        return True

    def _clear_typing_buffer(self, dt: float) -> None:
        """Reset incremental typing state after idle timeout."""
        self.typing_buffer = ""

    def _navigate_by_prefix(self, start: int, wrap: bool) -> None:
        """Move focus to the first label matching ``typing_buffer``.

        Args:
            start: Index to begin searching from.
            wrap: If True, continue searching from index 0 when no match is
                found from ``start`` to end.
        """
        size = self.state_machine.size()
        if size == 0:
            return

        labels = [
            cast(Element, state).label
            for state in self.state_machine.states.values()
        ]
        prefix = self.typing_buffer.lower()

        for index in range(start, size):
            if labels[index].lower().startswith(prefix):
                self.position = index
                self.activate_current_state()
                self.dispatch_event("on_change", self)
                return

        if wrap:
            wrapped_end = min(start, size)
            for index in range(0, wrapped_end):
                if labels[index].lower().startswith(prefix):
                    self.position = index
                    self.activate_current_state()
                    self.dispatch_event("on_change", self)
                    return

        self.dispatch_event("on_letter_navigation_fail", self)

    def activate_current_state(self, *args: Any, **kwargs: Any) -> None:
        """Activate the state associated with the current menu position."""
        self.state_machine.set_current_index(self.position)
        self.state_machine.activate_current_state(*args, **kwargs)

    def add(self, key: str, item: Element | str) -> None:
        """Add a menu item state from text or an Element instance."""
        if isinstance(item, str):
            self.state_machine.add(
                key,
                TextLabel(self, item, enable_shortcuts=False),
            )  # type: ignore
        elif isinstance(item, Element):
            # Menu owns UP/DOWN navigation; disable TextLabel shortcuts for
            # embedded labels so item handlers do not consume menu keys.
            if isinstance(item, TextLabel):
                item.use_key_handler = False
            self.state_machine.add(key, item)
        else:
            raise ValueError("Item must be either str or Element.")

    def remove(self, key: str) -> Optional[Element]:
        """Remove and return a menu item by key."""
        element: Optional[Element] = cast(
            Element, self.state_machine.remove(key)
        )
        return element

    # override
    def reset(self) -> None:
        """Restore default position and reset all menu item elements."""
        self.position = self.default_position
        self.state_machine.set_current_index(self.position)
        state_key: str = list(self.state_machine.states)[self.position]
        self.state_machine.current_state = self.state_machine.states[state_key]

        for item in self.state_machine.states.values():
            element_item: Element = cast(Element, item)
            element_item.reset()

    @property
    def active_element(self) -> Optional[State]:
        """Get the currently active menu item."""
        if self.state_machine.is_empty():
            return None
        return self.state_machine.current_state


Menu.register_event_type("on_change")
Menu.register_event_type("on_border")
Menu.register_event_type("on_submit")
Menu.register_event_type("on_letter_navigation_fail")
