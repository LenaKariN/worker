from __future__ import annotations
from collections.abc import Sequence

from punq import Container
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from employees.adapters.input.cli_builder import build_typer_app
from employees.application.messages import GROUP_EMPLOYEE
from employees.application.ports.input import Printable, Reader, UseCase


class CliAdapter(Printable):
    """
    Адаптер для консольного интерфейса (CLI).
    """

    def __init__(self, container: Container, usecases: Sequence[type[UseCase]]):
        # Сам адаптер остается тонким: вся логика построения команд вынесена
        # в builder, а здесь мы только создаем готовое Typer-приложение.
        self.container = container
        self.app = build_typer_app(container, tuple(usecases))

    def run(self, argv: Sequence[str] | None = None) -> int:
        """
        Точка входа в CLI.
        """

        command = typer.main.get_command(self.app)
        try:
            # standalone_mode=False позволяет не завершать процесс внутри Click,
            # а вернуть управление обратно в наше приложение с кодом выхода.
            result = command.main(
                args=list(argv) if argv is not None else None,
                prog_name=GROUP_EMPLOYEE,
                standalone_mode=False,
            )
        except typer.Exit as exc:
            return exc.exit_code
        except Exception as exc:
            if hasattr(exc, "show") and hasattr(exc, "exit_code"):
                exc.show()
                return exc.exit_code
            raise

        return 0 if result is None else int(result)

    def out(self, message: str) -> None:
        """
        Платформа-зависимый метод печати в консоли.
        """
        typer.echo(message)

    def render_table(
        self, title: str, columns: list[str], rows: list[list[str]]
    ) -> None:
        table = Table(title=title, show_header=True, header_style="bold")
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*row)
        console = Console()
        with console.capture() as capture:
            console.print(table)
        typer.echo(capture.get())

    def render_panel(self, title: str, fields: list[tuple[str, str]]) -> None:
        parts: list[str] = []
        for i, (label, value) in enumerate(fields):
            style = "[bold cyan]" if i == 0 else "[bold]"
            parts.append(f" {style}{label}:[/]         {value}")
        info = "\n".join(parts)
        console = Console()
        with console.capture() as capture:
            console.print(Panel(info, title=f"[bold]{title}[/]", border_style="blue"))
        typer.echo(capture.get())


class CliReader(Reader):
    """
    Адаптер для чтения пользовательского ввода из консоли.
    """

    def prompt(self, text: str) -> str:
        return input(text)
