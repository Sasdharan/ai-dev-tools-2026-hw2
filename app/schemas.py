from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Member(BaseModel):
    id: str
    name: str


class AddMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Member name must not be blank.")
        return value


class Group(BaseModel):
    id: str
    name: str
    closed: bool


class Expense(BaseModel):
    id: str
    desc: str
    amount: float = Field(gt=0)
    date: date
    participants: list[str] = Field(min_length=1)
    payer: str
    locked: bool


class AddExpenseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    desc: str = Field(min_length=1)
    amount: float = Field(gt=0)
    date: date
    participants: list[str] = Field(min_length=1)
    payer: str

    @field_validator("desc")
    @classmethod
    def description_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Expense description must not be blank.")
        return value


class Settlement(BaseModel):
    id: str
    from_: str = Field(alias="from")
    to: str
    amount: float = Field(gt=0)
    date: date
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class RecordSettlementRequest(BaseModel):
    from_: str = Field(alias="from")
    to: str
    amount: float = Field(gt=0)
    date: date
    notes: str | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AppState(BaseModel):
    group: Group
    members: list[Member]
    expenses: list[Expense]
    settlements: list[Settlement]


class ErrorResponse(BaseModel):
    detail: str
