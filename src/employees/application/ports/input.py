from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Description:
    """
    Описание параметров use case.
    """

    text: str


class UseCase(ABC):
    """
    Абстрактный базовый UseCase.
    """

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Выполняет пользовательский сценарий с его собственными параметрами."""

        # У каждого сценария своя сигнатура execute(...), а общий абстрактный
        # контракт нужен лишь для discovery и регистрации в контейнере.
        pass


class Printable(ABC):
    """
    Интерфейс печати сообщений.
    """

    @abstractmethod
    def out(self, message: str) -> None:
        """Выводит текст через выбранный внешний интерфейс."""
        pass

    @abstractmethod
    def render_table(
        self, title: str, columns: list[str], rows: list[list[str]]
    ) -> None:
        """Отрисовывает таблицу с заголовками колонок и строками данных."""

    @abstractmethod
    def render_panel(self, title: str, fields: list[tuple[str, str]]) -> None:
        """Отрисовывает панель с набором полей (метка, значение)."""


class Reader(ABC):
    """
    Интерфейс чтения пользовательского ввода.
    """

    @abstractmethod
    def prompt(self, text: str) -> str:
        """Выводит приглашение и возвращает строку, введённую пользователем."""
        pass
