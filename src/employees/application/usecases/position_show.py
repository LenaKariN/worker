from typing import Annotated

from employees.application.messages import (
    LABEL_NO,
    LABEL_YES,
    MSG_CODE_EMPTY,
    MSG_POSITION_NOT_FOUND_CODE,
    FMT_DATETIME,
    GROUP_POSITION,
    err,
)
from employees.application.ports.input import Description, Printable, UseCase
from employees.application.usecases.shared import fmt_dt, format_period, status_label
from employees.domain.ports.out import (
    EntityNotFoundError,
    PositionTypeRepository,
    TimeProvider,
)


class PositionShow(UseCase):
    """Показать детальную информацию о позиции."""

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
        code: Annotated[str, Description("Код позиции для просмотра")] = "",
    ) -> None:
        if not code:
            self.printer.out(err(MSG_CODE_EMPTY))
            return

        try:
            pt = self.repository.get_by_code(code)
        except EntityNotFoundError:
            self.printer.out(err(MSG_POSITION_NOT_FOUND_CODE.format(code=code)))
            return

        status = status_label(pt.effectivity, self.time_provider.now())
        deleted = LABEL_YES if pt.is_deleted else LABEL_NO
        period = format_period(pt.effectivity)

        fields = [
            ("Код:", pt.code),
            ("Наименование:", pt.name),
            ("Описание:", pt.description or "—"),
            ("Период действия:", period),
            ("Статус:", status),
            ("Удалена:", deleted),
            ("Создана:", fmt_dt(pt.created_at, FMT_DATETIME)),
            ("Обновлена:", fmt_dt(pt.updated_at, FMT_DATETIME)),
            ("ID:", str(pt.id)),
        ]

        self.printer.render_panel(pt.code, fields)
