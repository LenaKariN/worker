from __future__ import annotations

import shlex
import sys
from collections.abc import Sequence

from employees.composition_root import build_cli
from employees.adapters.input.cli import CliAdapter
from employees.application.messages import (
    MSG_PARSE_ERROR,
    MSG_EXIT_CODE,
    GROUP_EMPLOYEE,
)
from employees.ui.splash import show_splash

_QUIT_COMMANDS = ("exit", "quit", "q")
_HELP_COMMAND = "help"
_HELP_FLAGS = ["--help"]
_REPL_PROMPT = f"{GROUP_EMPLOYEE}> "
_REPL_GREETING = "Введите команду или 'help' для справки, 'quit' для выхода."


def _ensure_utf8_output() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run(argv: Sequence[str] | None = None) -> int:
    _ensure_utf8_output()
    show_splash()
    cli = build_cli()
    if argv is None and len(sys.argv) <= 1:
        return _repl(cli)
    return cli.run(argv)


def _repl(cli: CliAdapter) -> int:
    cli.out(_REPL_GREETING)
    while True:
        try:
            line = input(_REPL_PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            cli.out("")
            break
        if not line:
            continue
        if line in _QUIT_COMMANDS:
            break
        if line == _HELP_COMMAND:
            cli.run(_HELP_FLAGS)
            continue

        try:
            args = shlex.split(line)
        except ValueError as exc:
            cli.out(MSG_PARSE_ERROR.format(exc=exc))
            continue

        exit_code = cli.run(args)
        if exit_code != 0:
            cli.out(MSG_EXIT_CODE.format(exit_code=exit_code))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
