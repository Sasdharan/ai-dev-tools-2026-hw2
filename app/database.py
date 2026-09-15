from copy import deepcopy
from dataclasses import dataclass, field
from itertools import count
from typing import Any


@dataclass
class MockDatabase:
    group: dict[str, Any] = field(default_factory=dict)
    members: list[dict[str, Any]] = field(default_factory=list)
    expenses: list[dict[str, Any]] = field(default_factory=list)
    settlements: list[dict[str, Any]] = field(default_factory=list)
    _member_ids: Any = field(default_factory=lambda: count(3), repr=False)
    _expense_ids: Any = field(default_factory=lambda: count(1), repr=False)
    _settlement_ids: Any = field(default_factory=lambda: count(1), repr=False)

    def reset(self) -> None:
        self.group = {"id": "g1", "name": "Trip", "closed": False}
        self.members = [
            {"id": "m1", "name": "Alice"},
            {"id": "m2", "name": "Bob"},
        ]
        self.expenses = []
        self.settlements = []
        self._member_ids = count(3)
        self._expense_ids = count(1)
        self._settlement_ids = count(1)

    def new_member_id(self) -> str:
        return f"m{next(self._member_ids)}"

    def new_expense_id(self) -> str:
        return f"e{next(self._expense_ids)}"

    def new_settlement_id(self) -> str:
        return f"s{next(self._settlement_ids)}"

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(
            {
                "group": self.group,
                "members": self.members,
                "expenses": self.expenses,
                "settlements": self.settlements,
            }
        )


database = MockDatabase()
database.reset()


def reset_database() -> None:
    database.reset()
