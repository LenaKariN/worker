from typing import Annotated

from employees.application.messages import (
    MSG_ID_EMPTY,
    MSG_EMPLOYEE_NOT_FOUND,
    GROUP_EMPLOYEE,
    err,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.domain.ports.out import EmployeeRepository, EntityNotFoundError


class EmployeeDelete(UseCase):
    """Удалить сотрудника (мягкое удаление)."""

    __group__ = GROUP_EMPLOYEE

    def __init__(self, printer: Printable, repository: EmployeeRepository):
        self.printer = printer
        self.repository = repository

    def execute(
        self,
        id: Annotated[int | None, Description("ID удаляемого сотрудника")] = None,
    ) -> None:
        if id is None:
            self.printer.out(err(MSG_ID_EMPTY))
            return

        try:
            self.repository.soft_delete(id)
        except EntityNotFoundError:
            self.printer.out(err(MSG_EMPLOYEE_NOT_FOUND.format(id=id)))
            return

        self.printer.out(f"Сотрудник с id '{id}' помечен как удалённый.")
