from sonartk.util.text_history import TextHistory


def test_record_ignores_blank_entries() -> None:
    """Test that blank entries are ignored."""
    history = TextHistory()

    history.record("   ")

    assert history.entries == []
    assert history.index is None


def test_record_inserts_most_recent_first() -> None:
    """Test that the most recent entry is stored first."""
    history = TextHistory()

    history.record("first")
    history.record("second")

    assert history.entries == ["second", "first"]
    assert history.index is None


def test_record_enforces_limit() -> None:
    """Test that the history limit trims older entries."""
    history = TextHistory(limit=3)

    history.record("one")
    history.record("two")
    history.record("three")
    history.record("four")

    assert history.entries == ["four", "three", "two"]


def test_previous_value_returns_oldest_to_newest_order() -> None:
    """Test that previous_value walks older entries first."""
    history = TextHistory()
    history.record("one")
    history.record("two")
    history.record("three")

    assert history.previous_value() == "three"
    assert history.previous_value() == "two"
    assert history.previous_value() == "one"
    assert history.previous_value() == "one"


def test_next_value_moves_toward_blank_entry() -> None:
    """Test that next_value walks back toward a blank input."""
    history = TextHistory()
    history.record("one")
    history.record("two")

    assert history.previous_value() == "two"
    assert history.next_value() == ""
    assert history.next_value() is None


def test_clear_resets_navigation_cursor() -> None:
    """Test that clear resets navigation without dropping entries."""
    history = TextHistory()
    history.record("one")
    history.previous_value()

    history.clear()

    assert history.entries == ["one"]
    assert history.index is None
