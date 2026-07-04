from decimal import Decimal
from typing import Annotated

from employees.application.messages import (
    GROUP_EMPLOYEE,
    MSG_ID_NOT_SPECIFIED,
    MSG_EMPLOYEE_NOT_FOUND,
    MSG_FIELD_NOT_FOUND,
    MSG_LAST_NAME_EMPTY,
    MSG_FIRST_NAME_EMPTY,
    MSG_PHONE_EMPTY,
    MSG_POSITION_CODE_EMPTY,
    MSG_SALARY_MUST_BE_NUMBER,
    MSG_SALARY_NEGATIVE,
    MSG_DUPLICATE_EMPLOYEE_UPDATE,
    MSG_POSITION_NOT_FOUND,
    err,
)
from employees.application.ports.input import Description, Printable, Reader, UseCase
from employees.application.usecases.shared import (
    DateEndFieldEditor,
    DateStartFieldEditor,
    DecimalFieldEditor,
    FieldEditor,
    StringFieldEditor,
    fmt_dt,
    resolve_position_name,
    run_dialog,
)
from employees.domain.entities import Employee
from employees.domain.ports.out import (
    DuplicateEmployeeError,
    EmployeeRepository,
    EntityNotFoundError,
    PositionTypeRepository,
    TimeProvider,
)


class _PositionCodeFieldEditor(FieldEditor):
    def __init__(self, position_repository: PositionTypeRepository):
        self._repo = position_repository

    def edit(self, entity: object, value: str) -> str | None:
        value = value.strip()
        if not value:
            return MSG_POSITION_CODE_EMPTY
        try:
            self._repo.get_by_code(value)
        except EntityNotFoundError:
            return MSG_POSITION_NOT_FOUND.format(code=value)
        entity.position_code = value
        return None


class EmployeeUpdate(UseCase):
    """Изменить данные существующего сотрудника в диалоговом режиме."""

    __group__ = GROUP_EMPLOYEE

    _FIELD_LABELS = [
        "Фамилия",
        "Имя",
        "Отчество",
        "Телефон",
        "Зарплата",
        "Должность",
        "Начало",
        "Конец",
    ]

    def __init__(
        self,
        printer: Printable,
        reader: Reader,
        repository: EmployeeRepository,
        position_repository: PositionTypeRepository,
        time_provider: TimeProvider,
    ):
        self.printer = printer
        self.reader = reader
        self.repository = repository
        self.position_repository = position_repository
        self.time_provider = time_provider
        self._editors = self._build_field_editors()

    def _build_field_editors(self) -> list[FieldEditor]:
        return [
            StringFieldEditor(
                required=True,
                empty_error=MSG_LAST_NAME_EMPTY,
                setter=lambda e, v: setattr(e.person_name, "last_name", v),
            ),
            StringFieldEditor(
                required=True,
                empty_error=MSG_FIRST_NAME_EMPTY,
                setter=lambda e, v: setattr(e.person_name, "first_name", v),
            ),
            StringFieldEditor(
                required=False,
                setter=lambda e, v: setattr(e.person_name, "middle_name", v),
            ),
            StringFieldEditor(
                required=True,
                empty_error=MSG_PHONE_EMPTY,
                setter=lambda e, v: setattr(e.phone, "number", v),
            ),
            DecimalFieldEditor(
                min_value=Decimal(0),
                parse_error=MSG_SALARY_MUST_BE_NUMBER,
                negative_error=MSG_SALARY_NEGATIVE,
                setter=lambda e, v: setattr(e.salary, "amount", v),
            ),
            _PositionCodeFieldEditor(position_repository=self.position_repository),
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
        id: Annotated[int | None, Description("ID сотрудника для изменения")] = None,
    ) -> None:
        if id is None:
            self.printer.out(err(MSG_ID_NOT_SPECIFIED))
            return

        try:
            emp = self.repository.get_by_id(id)
        except EntityNotFoundError:
            self.printer.out(err(MSG_EMPLOYEE_NOT_FOUND.format(id=id)))
            return

        run_dialog(
            self.printer,
            self.reader,
            emp,
            self._FIELD_LABELS,
            self._build_rows,
            self._apply_field,
        )

        full_name = emp.person_name.full_name
        position_name = resolve_position_name(
            self.position_repository, emp.position_code
        )
        self.printer.out(f"Сотрудник изменён: {full_name} — {position_name}")

    def _build_rows(self, entity: Employee) -> list[tuple[str, str]]:
        return [
            ("Фамилия", entity.person_name.last_name),
            ("Имя", entity.person_name.first_name),
            ("Отчество", entity.person_name.middle_name or "—"),
            ("Телефон", entity.phone.number),
            ("Зарплата", str(entity.salary.amount)),
            (
                "Должность",
                resolve_position_name(self.position_repository, entity.position_code),
            ),
            ("Начало", fmt_dt(entity.effectivity.effective_from)),
            ("Конец", fmt_dt(entity.effectivity.effective_to)),
        ]

    def _apply_field(self, entity: Employee, field_no: int, value: str) -> str | None:
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
        except DuplicateEmployeeError:
            return MSG_DUPLICATE_EMPLOYEE_UPDATE
        return None
