from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import ValidationError

from employees.application.messages import (
    ERR_VALIDATION_PREFIX,
    MSG_DUPLICATE_EMPLOYEE,
    MSG_POSITION_NOT_FOUND,
    MSG_SALARY_MUST_BE_NUMBER,
    MSG_SALARY_NEGATIVE,
    GROUP_EMPLOYEE,
    err,
    validation_err,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.application.usecases.shared import (
    ensure_utc,
    resolve_position_name,
    status_label,
)
from employees.domain.entities import Effectivity, Employee, Money, PersonName, Phone
from employees.domain.ports.out import (
    DuplicateEmployeeError,
    EmployeeRepository,
    EntityNotFoundError,
    IdGenerator,
    PositionTypeRepository,
    TimeProvider,
)


class EmployeeCreate(UseCase):
    """Создать нового сотрудника."""

    __group__ = GROUP_EMPLOYEE
    __group_help__ = "Управление сотрудниками компании"

    def __init__(
        self,
        printer: Printable,
        repository: EmployeeRepository,
        position_repository: PositionTypeRepository,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ):
        self.printer = printer
        self.repository = repository
        self.position_repository = position_repository
        self.id_generator = id_generator
        self.time_provider = time_provider

    def execute(
        self,
        last_name: Annotated[str, Description("Фамилия сотрудника")] = "",
        first_name: Annotated[str, Description("Имя сотрудника")] = "",
        middle_name: Annotated[str, Description("Отчество сотрудника")] = "",
        phone: Annotated[str, Description("Номер телефона")] = "",
        salary: Annotated[str, Description("Зарплата сотрудника")] = "0",
        position: Annotated[
            str, Description("Код должности из справочника позиций")
        ] = "",
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
        dates = self._normalize_dates(effective_from, effective_to)
        parsed_salary = self._parse_salary(salary)
        if parsed_salary is None:
            return
        if not self._salary_is_not_negative(parsed_salary):
            return
        if not self._position_exists(position):
            return
        employee = self._build_employee(
            last_name, first_name, middle_name, phone, parsed_salary, position, dates
        )
        if employee is None:
            return
        if not self._persist(employee, last_name, first_name, phone):
            return
        self._print_created(employee, last_name, first_name, position)

    def _normalize_dates(
        self,
        effective_from: datetime | None,
        effective_to: datetime | None,
    ) -> tuple[datetime, datetime | None]:
        now = self.time_provider.now()
        from_dt = ensure_utc(effective_from) if effective_from is not None else now
        to_dt = ensure_utc(effective_to) if effective_to is not None else None
        return from_dt, to_dt

    def _parse_salary(self, salary_str: str) -> Decimal | None:
        try:
            return Decimal(salary_str)
        except (ValueError, ArithmeticError):
            self.printer.out(validation_err(MSG_SALARY_MUST_BE_NUMBER))
            return None

    def _salary_is_not_negative(self, salary: Decimal) -> bool:
        if salary < 0:
            self.printer.out(validation_err(MSG_SALARY_NEGATIVE))
            return False
        return True

    def _position_exists(self, position_code: str) -> bool:
        try:
            self.position_repository.get_by_code(position_code)
            return True
        except EntityNotFoundError:
            self.printer.out(err(MSG_POSITION_NOT_FOUND.format(code=position_code)))
            return False

    def _build_employee(
        self,
        last_name: str,
        first_name: str,
        middle_name: str,
        phone: str,
        salary: Decimal,
        position_code: str,
        dates: tuple[datetime, datetime | None],
    ) -> Employee | None:
        try:
            effectivity = Effectivity(effective_from=dates[0], effective_to=dates[1])
            return Employee(
                id=self.id_generator.next_id(),
                contacts=[
                    PersonName(
                        last_name=last_name.strip(),
                        first_name=first_name.strip(),
                        middle_name=middle_name.strip(),
                    ),
                    Phone(number=phone.strip()),
                ],
                salary=Money(amount=salary),
                position_code=position_code.strip(),
                effectivity=effectivity,
            )
        except ValidationError as exc:
            self.printer.out(f"{ERR_VALIDATION_PREFIX}: {exc}")
            return None

    def _persist(
        self,
        employee: Employee,
        last_name: str,
        first_name: str,
        phone: str,
    ) -> bool:
        try:
            self.repository.add_or_update(employee)
            return True
        except DuplicateEmployeeError:
            self.printer.out(
                err(
                    MSG_DUPLICATE_EMPLOYEE.format(
                        last_name=last_name, first_name=first_name, phone=phone
                    )
                )
            )
            return False

    def _print_created(
        self,
        employee: Employee,
        last_name: str,
        first_name: str,
        position_code: str,
    ) -> None:
        status = status_label(employee.effectivity, self.time_provider.now())
        self.printer.out(
            f"Создан сотрудник: {last_name} {first_name} — "
            f"{resolve_position_name(self.position_repository, position_code)} "
            f"(статус: {status}, id: {employee.id})"
        )
