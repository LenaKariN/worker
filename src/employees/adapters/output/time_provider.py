from datetime import datetime, timezone

from employees.domain.ports.out import TimeProvider


class UtcTimeProvider(TimeProvider):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
