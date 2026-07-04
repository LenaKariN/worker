from typing import Annotated

from employees.application.messages import (
    MSG_CODE_EMPTY,
    MSG_POSITION_NOT_FOUND_CODE,
    GROUP_POSITION,
    err,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.domain.ports.out import EntityNotFoundError, PositionTypeRepository


class PositionDelete(UseCase):
    """Удалить позицию из справочника (мягкое удаление)."""

    __group__ = GROUP_POSITION

    def __init__(self, printer: Printable, repository: PositionTypeRepository):
        self.printer = printer
        self.repository = repository

    def execute(
        self,
        code: Annotated[str, Description("Код удаляемой позиции")] = "",
    ) -> None:
        if not code:
            self.printer.out(err(MSG_CODE_EMPTY))
            return

        try:
            self.repository.soft_delete(code)
        except EntityNotFoundError:
            self.printer.out(err(MSG_POSITION_NOT_FOUND_CODE.format(code=code)))
            return

        self.printer.out(f"Позиция '{code}' помечена как удалённая.")
