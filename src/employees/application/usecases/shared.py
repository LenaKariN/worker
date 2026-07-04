from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal

from employees.application.messages import (
    FMT_DATE,
    NULL_PLACEHOLDER,
    MSG_DIALOG_PROMPT,
    MSG_DIALOG_INVALID_FORMAT,
    MSG_DIALOG_FIELD_NOT_NUMBER,
    MSG_DIALOG_UPDATED,
    MSG_INVALID_DATE_FORMAT,
    MSG_DATE_START_AFTER_END,
    MSG_DATE_END_BEFORE_START,
    LABEL_PRESENT_TIME,
    err,
)
from employees.application.ports.input import Printable, Reader
from employees.domain.constants import SECONDS_PER_YEAR, STATUS_ACTIVE, STATUS_INACTIVE
from employees.domain.ports.out import EntityNotFoundError, PositionTypeRepository


def status_label(effectivity: object, now: datetime) -> str:
    return STATUS_ACTIVE if effectivity.is_active(now) else STATUS_INACTIVE


def parse_date(value: str) -> datetime:
    return ensure_utc(datetime.fromisoformat(value))


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_tenure_years(employee, now: datetime) -> float:
    end_date = now
    if (
        not employee.effectivity.is_active(now)
        and employee.effectivity.effective_to is not None
    ):
        end_date = employee.effectivity.effective_to
    delta = end_date - employee.effectivity.effective_from
    return delta.total_seconds() / SECONDS_PER_YEAR


def format_tenure(years: float) -> str:
    total_months = round(years * 12)
    y = total_months // 12
    m = total_months % 12
    if y == 0 and m == 0:
        return "0 мес."
    parts = []
    if y > 0:
        parts.append(f"{y} г.")
    if m > 0:
        parts.append(f"{m} мес.")
    return " ".join(parts)


def resolve_position_name(repository: PositionTypeRepository, code: str) -> str:
    try:
        pt = repository.get_by_code(code)
        return pt.name if pt.name else code
    except EntityNotFoundError:
        return code


def fmt_dt(dt: datetime | None, fmt: str = FMT_DATE) -> str:
    if dt is None:
        return NULL_PLACEHOLDER
    return dt.strftime(fmt)


def format_period(effectivity: object) -> str:
    return (
        f"{fmt_dt(effectivity.effective_from)}"
        f" — {fmt_dt(effectivity.effective_to) if effectivity.effective_to is not None else LABEL_PRESENT_TIME}"
    )


def run_dialog(
    printer: Printable,
    reader: Reader,
    entity: object,
    field_labels: list[str],
    build_rows: Callable[..., list[tuple[str, str]]],
    apply_field: Callable[..., str | None],
) -> None:
    _show_fields(printer, build_rows(entity))
    while not _handle_dialog_input(printer, reader, entity, field_labels, apply_field):
        pass
    _show_fields(printer, build_rows(entity))


def _handle_dialog_input(
    printer: Printable,
    reader: Reader,
    entity: object,
    field_labels: list[str],
    apply_field: Callable[..., str | None],
) -> bool:
    """Обрабатывает одну строку ввода. Возвращает True, если диалог завершён."""
    line = reader.prompt(MSG_DIALOG_PROMPT).strip()
    if line in ("0", ""):
        return True
    parts = line.split(maxsplit=1)
    if len(parts) != 2:
        printer.out(MSG_DIALOG_INVALID_FORMAT)
        return False
    try:
        field_no = int(parts[0])
    except ValueError:
        printer.out(MSG_DIALOG_FIELD_NOT_NUMBER)
        return False
    if field_no < 1 or field_no > len(field_labels):
        printer.out(
            err(f"Нет поля с номером {field_no}. Допустимые: 1-{len(field_labels)}")
        )
        return False
    error = apply_field(entity, field_no, parts[1])
    if error:
        printer.out(err(error))
    else:
        printer.out(f"{field_labels[field_no - 1]}{MSG_DIALOG_UPDATED}")
    return False


def _show_fields(printer: Printable, rows: list[tuple[str, str]]) -> None:
    data_rows = [[str(i), field, value] for i, (field, value) in enumerate(rows, 1)]
    printer.render_table("", ["№", "Поле", "Значение"], data_rows)


# ═══════════════════════════════════════════════════════════════════════════════
# Редакторы полей для диалогового режима (FieldEditor pattern)
# ═══════════════════════════════════════════════════════════════════════════════


class FieldEditor(ABC):
    """Редактор одного поля сущности в диалоговом режиме."""

    @abstractmethod
    def edit(self, entity: object, value: str) -> str | None:
        """Валидирует и применяет значение. Возвращает сообщение об ошибке или None."""
        ...


class StringFieldEditor(FieldEditor):
    def __init__(
        self,
        *,
        required: bool = True,
        empty_error: str = "",
        max_length: int | None = None,
        max_length_error: str = "",
        setter: Callable[[object, str], None],
    ):
        self._required = required
        self._empty_error = empty_error
        self._max_length = max_length
        self._max_length_error = max_length_error
        self._set = setter

    def edit(self, entity: object, value: str) -> str | None:
        value = value.strip()
        if self._required and not value:
            return self._empty_error
        if self._max_length and len(value) > self._max_length:
            return self._max_length_error
        self._set(entity, value)
        return None


class DecimalFieldEditor(FieldEditor):
    def __init__(
        self,
        *,
        min_value: Decimal = Decimal(0),
        parse_error: str = "",
        negative_error: str = "",
        setter: Callable[[object, Decimal], None],
    ):
        self._min = min_value
        self._parse_error = parse_error
        self._negative_error = negative_error
        self._set = setter

    def edit(self, entity: object, value: str) -> str | None:
        try:
            amount = Decimal(value)
        except (ValueError, ArithmeticError):
            return self._parse_error
        if amount < self._min:
            return self._negative_error
        self._set(entity, amount)
        return None


class DateStartFieldEditor(FieldEditor):
    def __init__(
        self,
        *,
        get_effectivity: Callable[[object], object],
        set_from: Callable[[object, datetime], None],
        invalid_date_error: str = MSG_INVALID_DATE_FORMAT,
        start_after_end_error: str = MSG_DATE_START_AFTER_END,
    ):
        self._get_eff = get_effectivity
        self._set_from = set_from
        self._invalid_date_error = invalid_date_error
        self._start_after_end_error = start_after_end_error

    def edit(self, entity: object, value: str) -> str | None:
        try:
            dt = parse_date(value)
        except ValueError:
            return self._invalid_date_error
        eff = self._get_eff(entity)
        if eff.effective_to is not None and dt >= eff.effective_to:
            return self._start_after_end_error
        self._set_from(entity, dt)
        return None


class DateEndFieldEditor(FieldEditor):
    def __init__(
        self,
        *,
        get_effectivity: Callable[[object], object],
        set_to: Callable[[object, datetime | None], None],
        invalid_date_error: str = MSG_INVALID_DATE_FORMAT,
        end_before_start_error: str = MSG_DATE_END_BEFORE_START,
    ):
        self._get_eff = get_effectivity
        self._set_to = set_to
        self._invalid_date_error = invalid_date_error
        self._end_before_start_error = end_before_start_error

    def edit(self, entity: object, value: str) -> str | None:
        value = value.strip()
        if not value:
            self._set_to(entity, None)
            return None
        try:
            dt = parse_date(value)
        except ValueError:
            return self._invalid_date_error
        eff = self._get_eff(entity)
        if dt <= eff.effective_from:
            return self._end_before_start_error
        self._set_to(entity, dt)
        return None
