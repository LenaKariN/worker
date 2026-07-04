from __future__ import annotations

import inspect
import re
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from punq import Container
import typer

from employees.application.ports.input import Description, UseCase


def build_typer_app(
    container: Container, usecases: list[type[UseCase]] | tuple[type[UseCase], ...]
) -> typer.Typer:
    """Строит `Typer`-приложение из списка зарегистрированных use case."""

    app = typer.Typer(
        no_args_is_help=True,
        callback=_root_callback,
    )

    groups: dict[str, typer.Typer] = {}

    for usecase in usecases:
        command_help = inspect.getdoc(usecase) or None
        command = _build_command(container, usecase)
        group = getattr(usecase, "__group__", None)

        if group:
            command_name = _command_name_in_group(usecase.__name__, group)
            sub_app = groups.get(group)
            if sub_app is None:
                group_help = getattr(usecase, "__group_help__", None)
                sub_app = typer.Typer(no_args_is_help=True)
                groups[group] = (sub_app, group_help)
            else:
                sub_app = groups[group][0]
            sub_app.command(name=command_name, help=command_help)(command)
        else:
            command_name = _to_kebab_case(usecase.__name__)
            app.command(name=command_name, help=command_help)(command)

    for group_name, (sub_app, group_help) in groups.items():
        app.add_typer(sub_app, name=group_name, help=group_help)

    return app


def _build_command(container: Container, usecase_type: type[UseCase]):
    """Создает CLI-обертку над `execute()` конкретного use case."""

    signature = inspect.signature(usecase_type.execute)
    type_hints = get_type_hints(usecase_type.execute, include_extras=True)
    command_parameters = [
        _to_typer_parameter(
            parameter, type_hints.get(parameter.name, parameter.annotation)
        )
        for parameter in signature.parameters.values()
        if parameter.name != "self"
    ]

    typed_command: Any = _make_command_closure(container, usecase_type)
    typed_command.__name__ = usecase_type.__name__
    typed_command.__doc__ = inspect.getdoc(usecase_type)
    typed_command.__signature__ = inspect.Signature(
        parameters=command_parameters,
        return_annotation=_unwrap_annotated(
            type_hints.get("return", signature.return_annotation)
        ),
    )
    return typed_command


def _make_command_closure(container: Container, usecase_type: type[UseCase]) -> Any:
    """Фабрика замыкания: резолвит use case из контейнера и вызывает execute."""

    def command(**kwargs: Any) -> Any:
        usecase = container.resolve(usecase_type)
        return usecase.execute(**kwargs)

    return command


def _to_typer_parameter(
    parameter: inspect.Parameter,
    annotation: Any,
) -> inspect.Parameter:
    """Преобразует параметр `execute()` в параметр команды Typer."""

    default_value = parameter.default
    is_required = default_value is inspect.Parameter.empty
    parameter_annotation = _unwrap_annotated(annotation)
    help_text = _extract_help(annotation)
    show_default = not is_required
    kind = _detect_kind(parameter)

    if kind == "argument":
        typer_default = typer.Argument(
            ... if is_required else default_value,
            help=help_text,
            show_default=show_default,
        )
    else:
        typer_default = typer.Option(
            ... if is_required else default_value,
            _build_long_option(parameter.name),
            help=help_text,
            show_default=show_default,
        )

    return parameter.replace(
        annotation=parameter_annotation,
        default=typer_default,
    )


def _detect_kind(parameter: inspect.Parameter) -> str:
    """Определяет, будет ли параметр CLI аргументом или опцией."""

    if parameter.default is inspect.Parameter.empty:
        return "argument"
    return "option"


def _build_long_option(parameter_name: str) -> str:
    """Строит длинное имя CLI-опции из имени параметра Python."""

    return f"--{parameter_name.replace('_', '-')}"


def _extract_help(annotation: Any) -> str:
    """Извлекает текст help из metadata `Annotated`."""

    if get_origin(annotation) is Annotated:
        for metadata in get_args(annotation)[1:]:
            if isinstance(metadata, Description):
                return metadata.text
    return ""


def _unwrap_annotated(annotation: Any) -> Any:
    """Возвращает базовый тип из `Annotated`, если annotation обернута."""

    if get_origin(annotation) is Annotated:
        return get_args(annotation)[0]
    return annotation


def _to_kebab_case(name: str) -> str:
    """Преобразует имя класса в kebab-case имя CLI-команды."""

    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _command_name_in_group(class_name: str, group: str) -> str:
    """Вычисляет имя подкоманды внутри группы."""

    full = _to_kebab_case(class_name)
    prefix = group.lower() + "-"
    if full.startswith(prefix):
        return full[len(prefix) :]
    return full


def _root_callback() -> None:
    """Пустой callback корневой группы команд Typer."""

    return None
