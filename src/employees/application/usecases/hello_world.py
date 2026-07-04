from typing import Annotated

from employees.application.ports.input import Description, Printable, UseCase


class HelloWorld(UseCase):
    """Печатает приветствие."""

    _DEFAULT_NAME = "World"
    _GREETING = "Hello, {name}!"

    def __init__(self, printer: Printable):
        """Сохраняет порт вывода, через который use case пишет результат."""

        self.printer = printer

    def execute(
        self,
        # Description(...) не влияет на бизнес-логику use case.
        # Это только metadata для CLI-адаптера, чтобы показать help параметра.
        name: Annotated[str, Description("Имя для приветствия")] = _DEFAULT_NAME,
    ) -> None:
        """Печатает приветствие с именем, переданным пользователем."""

        self.printer.out(self._GREETING.format(name=name))
