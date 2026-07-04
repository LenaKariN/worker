from employees.domain.ports.out import IdGenerator


class IncrementalIdGenerator(IdGenerator):
    def __init__(self):
        self._counter = 0

    def next_id(self) -> int:
        self._counter += 1
        return self._counter
