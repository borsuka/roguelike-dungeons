"""Тестове за лога на съобщенията."""

from __future__ import annotations

from ui.message_log import MessageLog


def test_add_and_last() -> None:
    log = MessageLog()
    for i in range(5):
        log.add(f"съобщение {i}")
    assert [m.text for m in log.last(2)] == ["съобщение 3", "съобщение 4"]
    assert log.last(0) == []


def test_repeated_messages_are_stacked() -> None:
    log = MessageLog()
    log.add("Плъх те удря.")
    log.add("Плъх те удря.")
    log.add("Плъх те удря.")
    assert len(log) == 1
    assert log.messages[0].full_text == "Плъх те удря. (x3)"


def test_log_is_trimmed_to_max_size() -> None:
    log = MessageLog(max_messages=10)
    for i in range(25):
        log.add(f"m{i}")
    assert len(log) == 10
    assert log.messages[0].text == "m15"
