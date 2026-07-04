from typing import Annotated

from employees.application.messages import (
    MSG_NO_TENURE,
    MSG_PAGE_TENURE,
    GROUP_EMPLOYEE,
    SORT_UP,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.application.usecases.shared import (
    calculate_tenure_years,
    format_tenure,
    resolve_position_name,
    status_label,
)
from employees.domain.constants import ALL_RECORDS_PAGE_SIZE
from employees.domain.entities import Employee
from employees.domain.ports.out import (
    EmployeeRepository,
    PositionTypeRepository,
    TimeProvider,
)


class EmployeeTenure(UseCase):
    """Показать сотрудников со стажем более N лет."""

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
        years: Annotated[int, Description("Минимальный стаж в годах (строго больше)")],
        sort: Annotated[
            str,
            Description("Сортировка по стажу: up (возрастание) или down (убывание)"),
        ] = SORT_UP,
        page: Annotated[int, Description("Номер страницы")] = 1,
        page_size: Annotated[int, Description("Размер страницы")] = 20,
    ) -> None:
        all_employees = self._fetch_all_employees()
        tenure_data = self._compute_tenures(all_employees, years)
        if not tenure_data:
            self.printer.out(MSG_NO_TENURE.format(years=years))
            return

        page_items = self._sort_and_paginate(tenure_data, sort, page, page_size)
        rows = self._build_tenure_rows(page_items)
        columns = [
            "ID",
            "Фамилия",
            "Имя",
            "Должность",
            "Зарплата",
            "Телефон",
            "Статус",
            "Стаж",
        ]

        dir_label = "убыванию" if sort != SORT_UP else "возрастанию"
        self.printer.render_table(
            f"Сотрудники со стажем более {years} лет (по {dir_label} стажа)",
            columns,
            rows,
        )
        self.printer.out(MSG_PAGE_TENURE.format(page=page, total=len(tenure_data)))

    def _fetch_all_employees(self) -> list[Employee]:
        return self.repository.get_all(
            include_deleted=False,
            page=1,
            page_size=ALL_RECORDS_PAGE_SIZE,
        )

    def _compute_tenures(
        self, employees: list[Employee], threshold_years: int
    ) -> list[tuple[float, Employee]]:
        now = self.time_provider.now()
        result: list[tuple[float, Employee]] = []
        for emp in employees:
            t = calculate_tenure_years(emp, now)
            if t > threshold_years:
                result.append((t, emp))
        return result

    def _sort_and_paginate(
        self,
        tenure_data: list[tuple[float, Employee]],
        sort: str,
        page: int,
        page_size: int,
    ) -> list[tuple[float, Employee]]:
        reverse = sort != SORT_UP
        tenure_data.sort(key=lambda item: item[0], reverse=reverse)
        start = (page - 1) * page_size
        return tenure_data[start : start + page_size]

    def _build_tenure_rows(
        self, page_items: list[tuple[float, Employee]]
    ) -> list[list[str]]:
        now = self.time_provider.now()
        rows: list[list[str]] = []
        for tenure_years_val, emp in page_items:
            status = status_label(emp.effectivity, now)
            rows.append(
                [
                    str(emp.id),
                    emp.person_name.last_name,
                    emp.person_name.first_name,
                    resolve_position_name(self.position_repository, emp.position_code),
                    str(emp.salary.amount),
                    emp.phone.number,
                    status,
                    format_tenure(tenure_years_val),
                ]
            )
        return rows
