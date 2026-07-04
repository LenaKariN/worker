from __future__ import annotations

import typer

BANNER = """\
 _____ __  __ ____  _     _____   _______ _____ ____
| ____|  \\/  |  _ \\| |   / _ \\ \\ / / ____| ____/ ___|
|  _| | |\\/| | |_) | |  | | | \\ V /|  _| |  _| \\___ \\
| |___| |  | |  __/| |__| |_| || | | |___| |___ ___) |
|_____|_|  |_|_|   |_____\\___/ |_| |_____|_____|____/
"""

SUBTITLE = (
    "\u0423\u0447\u0435\u0431\u043d\u044b\u0439 \u043f\u0440\u043e\u0435\u043a\u0442 "
    "\u043f\u043e \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044e "
    "\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u043e\u043d\u043d\u043e\u0439 "
    "\u0441\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u043e\u0439"
)

SEPARATOR = "-" * 54


def show_splash() -> None:
    typer.echo("")
    typer.echo(typer.style(BANNER, fg=typer.colors.CYAN, bold=True))
    typer.echo(typer.style(SEPARATOR, fg=typer.colors.CYAN))
    typer.echo(typer.style(SUBTITLE, dim=True))
    typer.echo("")
