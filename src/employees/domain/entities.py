from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from employees.domain.constants import CODE_PATTERN, DEFAULT_CURRENCY


class Entity(BaseModel):
    """Абстрактная сущность предметной области."""

    model_config = ConfigDict(validate_assignment=True)

    id: int = Field(
        description="Уникальный идентификатор сущности (автоинкремент)",
    )
    is_deleted: bool = Field(
        default=False,
        description="Признак мягкого удаления. True — запись считается удалённой "
        "и не возвращается в списках по умолчанию",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Дата и время создания записи (UTC). "
        "Устанавливается однократно при создании сущности",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Дата и время последнего изменения записи (UTC). "
        "Обновляется при каждом сохранении",
    )


class Aggregate(Entity):
    """Маркерный класс: корень агрегата DDD."""

    pass


class Effectivity(BaseModel):
    """Период действия. Объект-значение, неизменяемый."""

    effective_from: datetime = Field(
        description="Начало периода действия (включительно). "
        "Может быть в прошлом для ретроспективного ввода",
    )
    effective_to: datetime | None = Field(
        default=None,
        description="Окончание периода действия (включительно). "
        "None — действует по настоящее время без ограничения срока",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "Effectivity":
        """Проверяет, что effective_from строго раньше effective_to (если задан)."""
        if self.effective_to is not None and self.effective_from >= self.effective_to:
            raise ValueError(
                f"effective_from ({self.effective_from}) должен быть раньше "
                f"effective_to ({self.effective_to})"
            )
        return self

    def is_active(self, at: datetime) -> bool:
        """Проверяет, действует ли период на указанный момент времени."""
        if self.effective_to is None:
            return self.effective_from <= at
        return self.effective_from <= at <= self.effective_to


class ReferenceType(Aggregate):
    """Абстрактный элемент справочника."""

    code: str = Field(
        min_length=1,
        description="Уникальный машиночитаемый код элемента справочника. "
        "Только латиница, цифры, подчёркивание. Пример: 'SENIOR_DEV'",
    )
    name: str = Field(
        min_length=1,
        max_length=200,
        description="Человекочитаемое наименование элемента. "
        "От 1 до 200 символов. Например: 'Старший разработчик'",
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Развёрнутое описание элемента. Опционально, до 2000 символов",
    )
    effectivity: Effectivity = Field(
        description="Период действия данного элемента справочника. "
        "Влияет на вычисление поля is_active",
    )

    @field_validator("code")
    @classmethod
    def _validate_code_format(cls, v: str) -> str:
        if not CODE_PATTERN.fullmatch(v):
            raise ValueError(
                "Код должен содержать только латиницу, цифры и подчёркивание"
            )
        return v


class PositionType(ReferenceType):
    """Тип позиции (должности) сотрудника в организации. Справочник."""

    pass


# Доменная модель основана на паттерне Accountability, описанным в книге
# "Analysis Patterns" (Martin Fowler).

# Объекты-значения, реализуют Microtype pattern, кандидаты в Shared Kernel


class Money(BaseModel):
    """
    Денежное значение (зарплата, бюджет, оборот).
    """

    amount: Decimal = Field(
        ge=0,
        description="Денежная сумма. Не может быть отрицательной",
    )
    currency: str = Field(
        default=DEFAULT_CURRENCY,
        description="Код валюты в формате ISO 4217",
    )


# Контакты, кандидаты в Shared Kernel


class Contact(BaseModel):
    """
    Абстрактный контакт. Базовый класс для Phone, PersonName, OrgName.
    Основан на паттерне Accountability (Martin Fowler, "Analysis Patterns").
    """

    pass


class PersonName(Contact):
    """ФИО сотрудника."""

    last_name: str = Field(
        min_length=1,
        description="Фамилия сотрудника",
    )
    first_name: str = Field(
        min_length=1,
        description="Имя сотрудника",
    )
    middle_name: str = Field(
        default="",
        description="Отчество сотрудника (опционально)",
    )

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)


class Phone(Contact):
    """Телефонный номер сотрудника."""

    number: str = Field(
        min_length=1,
        description="Номер телефона в произвольном формате",
    )


class OrgName(Contact):
    """Имя юридического лица."""

    name: str = Field(
        min_length=1,
        description="Наименование организации",
    )


# Доменные типы


class Party(Aggregate):
    """
    Абстрактная сущность, которая может участвовать в отношениях ответственности.
    Это могут быть как люди, так и целые подразделения.
    Является базовым классом для Employee и OrganizationalUnit.
    Основана на паттерне Accountability (Martin Fowler, "Analysis Patterns").
    """

    contacts: list[Contact] = Field(
        default_factory=list,
        min_length=1,
        description="Контактные данные стороны. Не менее одного контакта. "
        "Состав: PersonName, Phone и др.",
    )


# Кандидат в ограниченный контекст People
class Employee(Party):
    """
    Сотрудник компании (физическое лицо).
    """

    salary: Money = Field(
        description="Зарплата сотрудника",
    )
    position_code: str = Field(
        min_length=1,
        description="Код должности сотрудника из справочника PositionType",
    )
    effectivity: Effectivity = Field(
        description="Период действия записи о сотруднике. "
        "Определяет историчность данных в оргструктуре",
    )

    @property
    def person_name(self) -> PersonName:
        """Извлекает PersonName из списка контактов."""
        for contact in self.contacts:
            if isinstance(contact, PersonName):
                return contact
        raise ValueError("Сотрудник должен иметь контакт типа PersonName")

    @property
    def phone(self) -> Phone:
        """Извлекает Phone из списка контактов."""
        for contact in self.contacts:
            if isinstance(contact, Phone):
                return contact
        raise ValueError("Сотрудник должен иметь контакт типа Phone")

    def is_duplicate_of(self, other: "Employee") -> bool:
        return (
            self.person_name.last_name == other.person_name.last_name
            and self.person_name.first_name == other.person_name.first_name
            and self.phone.number == other.phone.number
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Заглушки для будущих FR (FR05: ОргЕдиницы, FR06: ОргСтруктура, FR07: Просмотр)
# ═══════════════════════════════════════════════════════════════════════════════


# Кандидат в ограниченный контекст Organization
class OrganizationalUnit(Party):
    """
    Организационная единица, подразделение (отдел, департамент, команда, проект).
    """

    pass


# Кандидат в ограниченный контекст Organization
class AccountabilityType(ReferenceType):
    """
    Тип отношения ответственности внутри организации.
    Справочник.
    """

    pass


# Кандидат в ограниченный контекст Organization
class UnitType(ReferenceType):
    """
    Тип подразделения организации (отдел, департамент, команда, проект).
    Справочник.
    """

    pass
