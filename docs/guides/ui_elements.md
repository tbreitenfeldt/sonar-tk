# UI Elements

This guide covers the newer UI element features: the multiline text viewer,
dialog helper functions, text input history, and text label keyboard shortcuts.

## MultilineTextBox

`MultilineTextBox` is a read-only, line-by-line text viewer. It extends
`TextBox` with line-aware navigation and announces each line through the screen
reader as the user moves through the content.

```python
from sonartk.ui.element import MultilineTextBox

viewer = MultilineTextBox(
    parent=screen,
    label="Log",
    default_value="First line\nSecond line\nThird line",
)
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Up | Previous line |
| Down | Next line |
| Home | Beginning of current line |
| End | End of current line |
| Ctrl+Home | Jump to first line |
| Ctrl+End | Jump to last line |
| Shift+Up | Extend selection to previous line |
| Shift+Down | Extend selection to next line |
| Ctrl+Shift+Left/Right | Word selection |
| Ctrl+C | Copy selection to clipboard |

### Updating Content

Assign to `value` to replace content at any time. The cursor returns to the
first line and the line buffer is rebuilt automatically.

```python
viewer.value = "Updated\nContent\nHere"
```

Call `speak_current_line()` to re-announce the current line from code without
moving the cursor.

### Line Change Event

Register an `on_line_change` handler to react whenever the focused line
changes.

```python
@viewer.event
def on_line_change(element: MultilineTextBox) -> None:
    print(f"Now on line {element.line_index}: {element.current_line}")
```

---

## Dialog Helpers

Three convenience functions in `sonartk.ui.screen` open common modal dialogs
without wiring up `Dialog`, `Button`, and `Menu` by hand.

### Alert Dialog

Speaks a message and provides a single confirmation button. The optional
`on_close` callback fires when the user dismisses the dialog or when the
dialog is closed programmatically.

```python
from sonartk.ui.screen import open_alert_dialog

open_alert_dialog(
    parent=screen,
    title="Notice",
    message="Your progress has been saved.",
    on_close=lambda: screen.change_state("main", None),
)
```

The `on_close` callback is guaranteed to fire exactly once regardless of how
the dialog is closed.

### Confirmation Dialog

Presents a message and a set of labeled choices. Each choice is paired with an
arbitrary return value. An optional cancel button resolves to `None`.

```python
from sonartk.ui.screen import open_confirmation_dialog

open_confirmation_dialog(
    parent=screen,
    title="Confirm",
    message="Are you sure you want to delete this save?",
    options=[("Yes, delete", True), ("No, keep it", False)],
    on_decision=lambda choice: handle_delete(choice),
    cancel_label="Cancel",  # set to None to omit the cancel button
)
```

`on_decision` receives the chosen value, or `None` if the user cancelled or
closed the dialog without choosing.

### Menu Selection Dialog

Opens a scrollable menu of string options and resolves to the selected index.
Returns `None` immediately (without opening a dialog) when `values` is empty.

```python
from sonartk.ui.screen import open_menu_selection_dialog

open_menu_selection_dialog(
    parent=screen,
    title="Choose Difficulty",
    label="Difficulty",
    values=["Easy", "Normal", "Hard"],
    on_selection=lambda index: apply_difficulty(index),
)
```

`on_selection` receives the integer index of the chosen item, or `None` if the
user cancelled. The callback fires after a short delay (default 0.35 s) to
allow the dialog to close before the next screen announces.

---

## TextBox Input History

`TextBox` supports optional command-history recall using Up and Down when
`enable_input_history=True`. This is useful for chat inputs, search bars, or
any field where the user may re-submit previous values.

```python
from sonartk.ui.element import TextBox

search_box = TextBox(
    parent=screen,
    label="Search",
    enable_input_history=True,
)
```

### Behaviour

- **Up** recalls the previous submitted value (most recent first).
- **Down** moves forward through history; pressing Down past the newest entry
  restores whatever the user was typing when they started navigating.
- Submitting an empty field does not add an entry to history.
- Consecutive duplicate submissions are deduplicated.
- History is per-instance and is not persisted between sessions.

### replace_value

`replace_value(value, announce=False)` replaces the field content
programmatically, resets caret position to the end, and clears any active
selection. Pass `announce=True` to speak the new value immediately.

```python
search_box.replace_value("default search", announce=True)
```

---

## TextHistory

`TextHistory` is a standalone utility dataclass for managing a bounded
most-recent-first history list. Use it when you need history navigation
outside of a `TextBox`.

```python
from sonartk.util import TextHistory

history = TextHistory(limit=100)
history.record("first command")
history.record("second command")

history.previous_value()  # "second command"
history.previous_value()  # "first command"
history.next_value()      # "second command"
history.next_value()      # ""  (back to editing state)
history.next_value()      # None (already past the bottom)
```

Call `clear()` to reset navigation state without dropping stored entries.

---

## TextLabel Keyboard Shortcuts

`TextLabel` now enables keyboard shortcuts by default. When focused, users can:

| Key | Action |
|-----|--------|
| Up / Down | Re-read the label |
| Ctrl+C | Copy the label text to the clipboard |

If you embed a `TextLabel` in a context where key ownership is managed
elsewhere (such as adding one directly to a `Menu`), pass
`enable_shortcuts=False` to suppress the bindings.

```python
from sonartk.ui.element import TextLabel

# Default: shortcuts enabled (suitable for standalone use on a Screen)
heading = TextLabel(screen, "Game Settings")

# Shortcuts disabled (for use inside Menu or other containers)
menu_label = TextLabel(screen, "Inventory", enable_shortcuts=False)
```

Note: when a `TextLabel` instance is added to a `Menu` via `Menu.add()`, its
shortcuts are disabled automatically so the menu retains full Up/Down
navigation control.

---

## Menu First-Letter Navigation

The first-letter navigation in `Menu` now responds immediately rather than
waiting for a timeout.

- **First character typed**: jumps immediately to the next item starting with
  that character after the current position, wrapping to the top if needed.
- **Same character repeated**: cycles through all items starting with that
  character.
- **Additional different characters before timeout**: refines the search from
  the beginning using the full prefix typed so far.
- After 0.4 s of inactivity the typing buffer is cleared, ready for a new
  sequence.

No code changes are required to take advantage of this; the behaviour is on by
default for all menus with `is_first_letter_navigation=True` (the default).
