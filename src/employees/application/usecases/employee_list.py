from typing import Annotated

from employees.application.messages import (
    LABEL_YES,
    MSG_EMPTY_EMPLOYEE_LIST,
    MSG_PAGE,
    GROUP_EMPLOYEE,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.application.usecases.shared import resolve_position_name, status_label
from employees.domain.ports.out import (
    EmployeeRepository,
    PositionTypeRepository,
    TimeProvider,
)


class EmployeeList(UseCase):
    """Показать список всех сотрудников."""

    __group__ = GROUP_EMPLOYEE

    def __init__(
        self,
        printer: Printable,
        repository: EmployeeRepository,
        position_repository: PositionTypeRepository,
        time_provider: TimeProvider,
    ):
        self.printer = printer
        self.repository = repository
        self.position_repository = position_repository
        self.time_provider = time_provider

    def execute(
        self,
        include_deleted: Annotated[
            bool, Description("Включить в список мягко-удалённых сотрудников")
        ] = False,
        page: Annotated[int, Description("Номер страницы")] = 1,
        page_size: Annotated[int, Description("Размер страницы")] = 20,
    ) -> None:
        employees = self.repository.get_all(
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )

        if not employees:
            self.printer.out(MSG_EMPTY_EMPLOYEE_LIST)
            return

        columns = [
            "ID",
            "Фамилия",
            "Имя",
            "Должность",
            "Зарплата",
            "Телефон",
            "Статус",
            "Удалён",
        ]
        rows: list[list[str]] = []
        for emp in employees:
            rows.append(self._build_employee_row(emp))

        self.printer.render_table("Сотрудники компании", columns, rows)
        self.printer.out(MSG_PAGE.format(page=page))

    def _build_employee_row(self, emp: object) -> list[str]:
        status = status_label(emp.effectivity, self.time_provider.now())
        deleted = LABEL_YES if emp.is_deleted else ""
        return [
            str(emp.id),
            emp.person_name.last_name,
            emp.person_name.first_name,
            resolve_position_name(self.position_repository, emp.position_code),
            str(emp.salary.amount),
            emp.phone.number,
            status,
            deleted,
        ]
