from typing import Annotated

from pydantic import ValidationError

from employees.application.messages import (
    GROUP_POSITION,
    MSG_CODE_NOT_SPECIFIED,
    MSG_POSITION_NOT_FOUND_CODE,
    MSG_FIELD_NOT_FOUND,
    MSG_NAME_EMPTY,
    MSG_NAME_TOO_LONG,
    MSG_DESCRIPTION_TOO_LONG,
    MSG_CANNOT_CHANGE_REFERENCED_CODE,
    MSG_DUPLICATE_CODE,
    err,
)
from employees.application.ports.input import Description, Printable, Reader, UseCase
from employees.application.usecases.shared import (
    DateEndFieldEditor,
    DateStartFieldEditor,
    FieldEditor,
    StringFieldEditor,
    fmt_dt,
    run_dialog,
)
from employees.domain.entities import PositionType
from employees.domain.ports.out import (
    DuplicateCodeError,
    EmployeeRepository,
    EntityNotFoundError,
    PositionTypeRepository,
    TimeProvider,
)


class _PositionCodeEditor(FieldEditor):
    def __init__(
        self,
        position_repository: PositionTypeRepository,
        employee_repository: EmployeeRepository,
    ):
        self._pos_repo = position_repository
        self._emp_repo = employee_repository

    def edit(self, entity: object, value: str) -> str | None:
        value = value.strip()
        if value != entity.code:
            if self._emp_repo.has_references_to_position(entity.code):
                return MSG_CANNOT_CHANGE_REFERENCED_CODE.format(code=entity.code)
        try:
            entity.code = value
        except ValidationError as exc:
            return str(exc)
        return None


class PositionUpdate(UseCase):
    """Изменить существующую позицию в справочнике должностей в диалоговом режиме."""

    __group__ = GROUP_POSITION

    _FIELD_LABELS = [
        "Код",
        "Наименование",
        "Описание",
        "Начало",
        "Конец",
    ]

    def __init__(
        self,
        printer: Printable,
        reader: Reader,
        repository: PositionTypeRepository,
        employee_repository: EmployeeRepository,
        time_provider: TimeProvider,
    ):
        self.printer = printer
        self.reader = reader
        self.repository = repository
        self.employee_repository = employee_repository
        self.time_provider = time_provider
        self._editors = self._build_field_editors()

    def _build_field_editors(self) -> list[FieldEditor]:
        return [
            _PositionCodeEditor(
                position_repository=self.repository,
                employee_repository=self.employee_repository,
            ),
            StringFieldEditor(
                required=True,
                empty_error=MSG_NAME_EMPTY,
                max_length=200,
                max_length_error=MSG_NAME_TOO_LONG,
                setter=lambda e, v: setattr(e, "name", v),
            ),
            StringFieldEditor(
                required=False,
                max_length=2000,
                max_length_error=MSG_DESCRIPTION_TOO_LONG,
                setter=lambda e, v: setattr(e, "description", v),
            ),
            DateStartFieldEditor(
                get_effectivity=lambda e: e.effectivity,
                set_from=lambda e, dt: setattr(e.effectivity, "effective_from", dt),
            ),
            DateEndFieldEditor(
                get_effectivity=lambda e: e.effectivity,
                set_to=lambda e, dt: setattr(e.effectivity, "effective_to", dt),
            ),
        ]

    def execute(
        self,
        code: Annotated[str, Description("Код изменяемой позиции")] = "",
    ) -> None:
        if not code:
            self.printer.out(err(MSG_CODE_NOT_SPECIFIED))
            return

        try:
            pt = self.repository.get_by_code(code)
        except EntityNotFoundError:
            self.printer.out(err(MSG_POSITION_NOT_FOUND_CODE.format(code=code)))
            return

        run_dialog(
            self.printer,
            self.reader,
            pt,
            self._FIELD_LABELS,
            self._build_rows,
            self._apply_field,
        )

        self.printer.out(f"Позиция изменена: {pt.code} — {pt.name}")

    def _build_rows(self, entity: PositionType) -> list[tuple[str, str]]:
        return [
            ("Код", entity.code),
            ("Наименование", entity.name),
            ("Описание", entity.description or "—"),
            ("Начало", fmt_dt(entity.effectivity.effective_from)),
            ("Конец", fmt_dt(entity.effectivity.effective_to)),
        ]

    def _apply_field(
        self, entity: PositionType, field_no: int, value: str
    ) -> str | None:
        if field_no < 1 or field_no > len(self._editors):
            return MSG_FIELD_NOT_FOUND.format(
                field_no=field_no, valid_range=f"1-{len(self._editors)}"
            )
        editor = self._editors[field_no - 1]
        error = editor.edit(entity, value)
        if error:
            return error
        entity.updated_at = self.time_provider.now()
        try:
            self.repository.add_or_update(entity)
        except DuplicateCodeError:
            return MSG_DUPLICATE_CODE.format(code=entity.code)
        return None
