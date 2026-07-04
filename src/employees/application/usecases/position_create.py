from datetime import datetime
from typing import Annotated, Optional

from pydantic import ValidationError

from employees.application.messages import (
    ERR_VALIDATION_PREFIX,
    MSG_DUPLICATE_POSITION,
    GROUP_POSITION,
    err,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.application.usecases.shared import ensure_utc, status_label
from employees.domain.entities import Effectivity, PositionType
from employees.domain.ports.out import (
    DuplicateCodeError,
    EntityNotFoundError,
    IdGenerator,
    PositionTypeRepository,
    TimeProvider,
)


class PositionCreate(UseCase):
    """Создать новую позицию в справочнике должностей."""

    __group__ = GROUP_POSITION
    __group_help__ = "Управление справочником должностей сотрудников"

    def __init__(
        self,
        printer: Printable,
        repository: PositionTypeRepository,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ):
        self.printer = printer
        self.repository = repository
        self.id_generator = id_generator
        self.time_provider = time_provider

    def execute(
        self,
        code: Annotated[
            str, Description("Уникальный код позиции (латиница, цифры, подчёркивание)")
        ] = "",
        name: Annotated[str, Description("Наименование позиции")] = "",
        description: Annotated[str, Description("Описание позиции")] = "",
        effective_from: Annotated[
            Optional[datetime],
            Description("Дата начала действия (YYYY-MM-DD), по умолчанию — текущая"),
        ] = None,
        effective_to: Annotated[
            Optional[datetime],
            Description(
                "Дата окончания действия (YYYY-MM-DD), по умолчанию — без ограничения"
            ),
        ] = None,
    ) -> None:
        now = self.time_provider.now()
        effective_from = (
            ensure_utc(effective_from) if effective_from is not None else now
        )
        effective_to = ensure_utc(effective_to) if effective_to is not None else None

        try:
            effectivity = Effectivity(
                effective_from=effective_from, effective_to=effective_to
            )
            position = PositionType(
                id=self.id_generator.next_id(),
                code=code,
                name=name.strip(),
                description=description.strip(),
                effectivity=effectivity,
            )
        except ValidationError as exc:
            self.printer.out(f"{ERR_VALIDATION_PREFIX}: {exc}")
            return

        try:
            self.repository.get_by_code(code)
            self.printer.out(err(MSG_DUPLICATE_POSITION.format(code=code)))
            return
        except EntityNotFoundError:
            pass

        try:
            self.repository.add_or_update(position)
        except DuplicateCodeError:
            self.printer.out(err(MSG_DUPLICATE_POSITION.format(code=code)))
            return

        status = status_label(effectivity, now)
        self.printer.out(f"Создана позиция: {code} — {name} (статус: {status})")
