from typing import Annotated

from employees.application.messages import (
    LABEL_NO,
    LABEL_YES,
    MSG_ID_EMPTY,
    MSG_EMPLOYEE_NOT_FOUND,
    FMT_DATETIME,
    GROUP_EMPLOYEE,
    err,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.application.usecases.shared import (
    fmt_dt,
    format_period,
    resolve_position_name,
    status_label,
)
from employees.domain.ports.out import (
    EmployeeRepository,
    EntityNotFoundError,
    PositionTypeRepository,
    TimeProvider,
)


class EmployeeShow(UseCase):
    """Показать детальную информацию о сотруднике."""

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
        id: Annotated[int | None, Description("ID сотрудника для просмотра")] = None,
    ) -> None:
        if id is None:
            self.printer.out(err(MSG_ID_EMPTY))
            return

        try:
            emp = self.repository.get_by_id(id)
        except EntityNotFoundError:
            self.printer.out(err(MSG_EMPLOYEE_NOT_FOUND.format(id=id)))
            return

        full_name = emp.person_name.full_name
        fields = self._build_employee_fields(emp)

        self.printer.render_panel(full_name, fields)

    def _build_employee_fields(self, emp: object) -> list[tuple[str, str]]:
        status = status_label(emp.effectivity, self.time_provider.now())
        deleted = LABEL_YES if emp.is_deleted else LABEL_NO
        period = format_period(emp.effectivity)
        full_name = emp.person_name.full_name

        return [
            ("ФИО:", full_name),
            ("Телефон:", emp.phone.number),
            (
                "Должность:",
                resolve_position_name(self.position_repository, emp.position_code),
            ),
            ("Зарплата:", f"{emp.salary.amount} {emp.salary.currency}"),
            ("Период действия:", period),
            ("Статус:", status),
            ("Удалён:", deleted),
            ("Создан:", fmt_dt(emp.created_at, FMT_DATETIME)),
            ("Обновлён:", fmt_dt(emp.updated_at, FMT_DATETIME)),
            ("ID:", str(emp.id)),
        ]
