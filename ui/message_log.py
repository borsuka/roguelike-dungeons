"""Лог на съобщенията (без pygame – рисуването е в ui/hud.py)."""

from __future__ import annotations

from dataclasses import dataclass

import config
from config import Color


@dataclass
class Message:
    """Едно съобщение.

    Attributes:
        text: Текстът.
        color: Цвят при рисуване.
        count: Колко пъти подред е повторено (показва се като "x3").
    """

    text: str
    color: Color
    count: int = 1

    @property
    def full_text(self) -> str:
        """Текстът с брояча на повторенията."""
        return f"{self.text} (x{self.count})" if self.count > 1 else self.text


class MessageLog:
    """Списък със съобщения; еднакви поредни съобщения се обединяват.

    Attributes:
        messages: Всички съобщения, най-новото е последно.
        max_messages: Колко най-много пазим (по-старите се изтриват).
    """

    def __init__(self, max_messages: int = config.LOG_MAX_MESSAGES) -> None:
        self.messages: list[Message] = []
        self.max_messages = max_messages

    def add(self, text: str, color: Color = config.COLOR_MSG_DEFAULT, stack: bool = True) -> None:
        """Добавя съобщение (или увеличава брояча, ако е същото като последното)."""
        if stack and self.messages and self.messages[-1].text == text:
            self.messages[-1].count += 1
            return
        self.messages.append(Message(text, color))
        if len(self.messages) > self.max_messages:
            del self.messages[: len(self.messages) - self.max_messages]

    def last(self, count: int) -> list[Message]:
        """Последните `count` съобщения (от по-старо към по-ново)."""
        return self.messages[-count:] if count > 0 else []

    def __len__(self) -> int:
        return len(self.messages)
