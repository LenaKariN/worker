from collections.abc import Callable, Hashable
from typing import Any, List, TypeVar

from employees.domain.entities import Employee, PositionType
from employees.domain.ports.out import (
    DuplicateCodeError,
    DuplicateEmployeeError,
    EmployeeRepository,
    EntityNotFoundError,
    PositionTypeRepository,
    TimeProvider,
)

_T = TypeVar("_T")
_K = TypeVar("_K", bound=Hashable)


def _paginate(
    items: list[_T],
    sort_key: Callable[[_T], Any],
    include_deleted: bool,
    page: int,
    page_size: int,
) -> list[_T]:
    if not include_deleted:
        items = [item for item in items if not item.is_deleted]  # type: ignore[attr-defined]
    sorted_items = sorted(items, key=sort_key)
    start = (page - 1) * page_size
    return sorted_items[start : start + page_size]


def _get_or_raise(
    store: dict[_K, Any],
    key: _K,
    entity_name: str,
) -> Any:
    entity = store.get(key)
    if entity is None or entity.is_deleted:
        raise EntityNotFoundError(entity_name, key)
    return entity


class InMemoryEmployeeRepository(EmployeeRepository):
    def __init__(self, time_provider: TimeProvider):
        self._store: dict[int, Employee] = {}
        self._time_provider = time_provider

    def add_or_update(self, entity: Employee) -> None:
        for existing in self._store.values():
            if existing.id == entity.id:
                continue
            if existing.is_deleted:
                continue
            if existing.is_duplicate_of(entity):
                raise DuplicateEmployeeError(
                    entity.person_name.last_name,
                    entity.person_name.first_name,
                    entity.phone.number,
                )
        entity.updated_at = self._time_provider.now()
        self._store[entity.id] = entity

    def get_all(
        self,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Employee]:
        return _paginate(
            list(self._store.values()),
            sort_key=lambda item: item.person_name.last_name,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )

    def get_by_id(self, employee_id: int) -> Employee:
        return _get_or_raise(self._store, employee_id, "Employee")

    def soft_delete(self, employee_id: int) -> None:
        entity = _get_or_raise(self._store, employee_id, "Employee")
        entity.is_deleted = True
        entity.updated_at = self._time_provider.now()

    def has_references_to_position(self, code: str) -> bool:
        return any(emp.position_code == code for emp in self._store.values())


class InMemoryPositionTypeRepository(PositionTypeRepository):
    def __init__(self, time_provider: TimeProvider):
        self._store: dict[str, PositionType] = {}
        self._time_provider = time_provider

    def add_or_update(self, entity: PositionType) -> None:
        for key, existing in list(self._store.items()):
            if existing.id == entity.id and key != entity.code:
                del self._store[key]
        existing = self._store.get(entity.code)
        if (
            existing is not None
            and existing.id != entity.id
            and not existing.is_deleted
        ):
            raise DuplicateCodeError(entity.code)
        entity.updated_at = self._time_provider.now()
        self._store[entity.code] = entity

    def get_all(
        self,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> List[PositionType]:
        return _paginate(
            list(self._store.values()),
            sort_key=lambda item: item.code,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )

    def get_by_code(self, code: str) -> PositionType:
        return _get_or_raise(self._store, code, "PositionType")

    def soft_delete(self, code: str) -> None:
        entity = _get_or_raise(self._store, code, "PositionType")
        entity.is_deleted = True
        entity.updated_at = self._time_provider.now()
