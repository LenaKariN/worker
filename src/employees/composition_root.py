from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Sequence

from punq import Container

from employees.adapters.input.cli import CliAdapter, CliReader
from employees.application.ports.input import Printable, Reader, UseCase
from employees.adapters.output.in_memory_repository import (
    InMemoryEmployeeRepository,
    InMemoryPositionTypeRepository,
)
from employees.adapters.output.time_provider import UtcTimeProvider
from employees.adapters.output.id_generator import IncrementalIdGenerator
from employees.domain.ports.out import (
    EmployeeRepository,
    IdGenerator,
    PositionTypeRepository,
    TimeProvider,
)

_USECASES_PACKAGE = "employees.application.usecases"


def discover_usecases() -> tuple[type[UseCase], ...]:
    """Находит все конкретные наследники `UseCase` в пакете application.usecases."""

    import employees.application.usecases as usecases_package

    usecases: dict[str, type[UseCase]] = {}
    for module_info in pkgutil.walk_packages(
        usecases_package.__path__,
        f"{_USECASES_PACKAGE}.",
    ):
        module = importlib.import_module(module_info.name)
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate.__module__ != module.__name__:
                continue
            if candidate is UseCase or not issubclass(candidate, UseCase):
                continue
            if inspect.isabstract(candidate):
                continue

            usecases[candidate.__name__] = candidate

    return tuple(sorted(usecases.values(), key=lambda item: item.__name__))


def build_container(
    usecases: Sequence[type[UseCase]] | None = None,
    *,
    employee_repository: EmployeeRepository | None = None,
    position_repository: PositionTypeRepository | None = None,
    id_generator: IdGenerator | None = None,
    time_provider: TimeProvider | None = None,
) -> Container:
    """Собирает IoC-контейнер с инфраструктурными зависимостями и use case."""

    container = Container()

    time_provider_instance = time_provider or UtcTimeProvider()

    container.register(
        EmployeeRepository,
        InMemoryEmployeeRepository,
        instance=employee_repository
        or InMemoryEmployeeRepository(time_provider_instance),
    )
    container.register(
        PositionTypeRepository,
        InMemoryPositionTypeRepository,
        instance=position_repository
        or InMemoryPositionTypeRepository(time_provider_instance),
    )
    container.register(
        IdGenerator,
        IncrementalIdGenerator,
        instance=id_generator or IncrementalIdGenerator(),
    )
    container.register(
        TimeProvider,
        UtcTimeProvider,
        instance=time_provider_instance,
    )
    for usecase in usecases or discover_usecases():
        container.register(usecase)
    return container


def build_cli() -> CliAdapter:
    """Создает CLI-адаптер и связывает его с контейнером как `Printable`."""

    usecases = discover_usecases()
    container = build_container(usecases)

    # CLI создается вручную, потому что сам адаптер нужен как зависимость
    # Printable для use case, которые печатают результат в консоль.
    cli = CliAdapter(container=container, usecases=usecases)
    container.register(Printable, instance=cli)
    container.register(CliAdapter, instance=cli)
    container.register(Reader, instance=CliReader())
    return cli
