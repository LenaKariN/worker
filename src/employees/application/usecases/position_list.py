from typing import Annotated

from employees.application.messages import (
    LABEL_YES,
    MSG_EMPTY_POSITION_LIST,
    MSG_PAGE,
    GROUP_POSITION,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.application.usecases.shared import status_label
from employees.domain.ports.out import PositionTypeRepository, TimeProvider


class PositionList(UseCase):
    """Показать список всех позиций справочника."""

    __group__ = GROUP_POSITION

    def __init__(
        self,
        printer: Printable,
        repository: PositionTypeRepository,
        time_provider: TimeProvider,
    ):
        self.printer = printer
        self.repository = repository
        self.time_provider = time_provider

    def execute(
        self,
        include_deleted: Annotated[
            bool, Description("Включить в список мягко-удалённые позиции")
        ] = False,
        page: Annotated[int, Description("Номер страницы")] = 1,
        page_size: Annotated[int, Description("Размер страницы")] = 20,
    ) -> None:
        positions = self.repository.get_all(
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )

        if not positions:
            self.printer.out(MSG_EMPTY_POSITION_LIST)
            return

        now = self.time_provider.now()
        columns = ["ID", "Код", "Наименование", "Статус", "Удалена"]
        rows: list[list[str]] = []
        for pt in positions:
            status = status_label(pt.effectivity, now)
            deleted = LABEL_YES if pt.is_deleted else ""
            rows.append([str(pt.id), pt.code, pt.name, status, deleted])

        self.printer.render_table("Справочник должностей", columns, rows)
        self.printer.out(MSG_PAGE.format(page=page))
