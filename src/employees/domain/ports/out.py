from abc import abstractmethod
from datetime import datetime
from typing import List, Protocol

from employees.domain.entities import Employee, PositionType


class IdGenerator(Protocol):
    @abstractmethod
    def next_id(self) -> int: ...


class TimeProvider(Protocol):
    @abstractmethod
    def now(self) -> datetime: ...


class EmployeeRepository(Protocol):
    """
    Репозиторий для сущности Employee.
    """

    @abstractmethod
    def add_or_update(self, entity: Employee) -> None:
        """
        Обновляет в репозитории существующий Employee или добавляет новый, если его нет.
        :exception DuplicateEmployeeError
        """
        pass

    @abstractmethod
    def get_all(
        self,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Employee]:
        """
        Возвращает страницу сотрудников.
        Если include_deleted=False, мягко-удалённые записи не возвращаются.
        """
        pass

    @abstractmethod
    def get_by_id(self, employee_id: int) -> Employee:
        """
        Возвращает Employee по его идентификатору.
        :exception EntityNotFoundError
        """
        pass

    @abstractmethod
    def soft_delete(self, employee_id: int) -> None:
        """
        Помечает сотрудника как удалённого (мягкое удаление).
        :exception EntityNotFoundError
        """
        pass

    @abstractmethod
    def has_references_to_position(self, code: str) -> bool:
        """
        Проверяет, ссылается ли хотя бы один сотрудник на указанный код позиции.
        """
        pass


class PositionTypeRepository(Protocol):
    """
    Репозиторий для сущности PositionType (справочник должностей/позиций).
    """

    @abstractmethod
    def add_or_update(self, entity: PositionType) -> None:
        """
        Обновляет существующую позицию или добавляет новую.
        """
        pass

    @abstractmethod
    def get_all(
        self,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> List[PositionType]:
        """
        Возвращает страницу позиций.
        Если include_deleted=False, мягко-удалённые записи не возвращаются.
        """
        pass

    @abstractmethod
    def get_by_code(self, code: str) -> PositionType:
        """
        Возвращает позицию по её уникальному коду.
        :exception EntityNotFoundError
        """
        pass

    @abstractmethod
    def soft_delete(self, code: str) -> None:
        """
        Помечает позицию как удалённую (мягкое удаление).
        :exception EntityNotFoundError
        """
        pass


class EntityNotFoundError(Exception):
    def __init__(self, entity_name, entity_id):
        super().__init__(f"{entity_name} с id={entity_id} не найден")


class DuplicateCodeError(Exception):
    def __init__(self, code: str):
        super().__init__(f"Элемент с кодом '{code}' уже существует")


class DuplicateEmployeeError(Exception):
    def __init__(self, last_name: str, first_name: str, phone: str):
        super().__init__(
            f"Сотрудник '{last_name} {first_name}' с телефоном '{phone}' уже существует"
        )
