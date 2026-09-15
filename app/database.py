import os
from collections.abc import Generator
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, ForeignKey, Numeric, String, Table, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


expense_participants = Table(
    "expense_participants",
    Base.metadata,
    Column("expense_id", ForeignKey("expenses.id", ondelete="CASCADE"), primary_key=True),
    Column("member_id", ForeignKey("members.id", ondelete="CASCADE"), primary_key=True),
)


class GroupRecord(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class MemberRecord(Base):
    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class ExpenseRecord(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    desc: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    payer_id: Mapped[str] = mapped_column(ForeignKey("members.id"), nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payer: Mapped[MemberRecord] = relationship(foreign_keys=[payer_id])
    participants: Mapped[list[MemberRecord]] = relationship(secondary=expense_participants)


class SettlementRecord(Base):
    __tablename__ = "settlements"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    from_id: Mapped[str] = mapped_column(ForeignKey("members.id"), nullable=False)
    to_id: Mapped[str] = mapped_column(ForeignKey("members.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    from_member: Mapped[MemberRecord] = relationship(foreign_keys=[from_id])
    to_member: Mapped[MemberRecord] = relationship(foreign_keys=[to_id])


database_url = os.getenv("DATABASE_URL", "sqlite:///./closetab.db")
engine_options = {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}
database_engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(bind=database_engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def next_id(session: Session, model: type[Base], prefix: str) -> str:
    records = session.scalars(select(model)).all()
    numbers = [
        int(record.id.removeprefix(prefix))
        for record in records
        if record.id.removeprefix(prefix).isdigit()
    ]
    return f"{prefix}{max(numbers, default=0) + 1}"


def member_dict(member: MemberRecord) -> dict[str, str]:
    return {"id": member.id, "name": member.name}


def expense_dict(expense: ExpenseRecord) -> dict:
    return {
        "id": expense.id,
        "desc": expense.desc,
        "amount": float(expense.amount),
        "date": expense.date,
        "participants": [member.id for member in expense.participants],
        "payer": expense.payer_id,
        "locked": expense.locked,
    }


def settlement_dict(settlement: SettlementRecord) -> dict:
    return {
        "id": settlement.id,
        "from": settlement.from_id,
        "to": settlement.to_id,
        "amount": float(settlement.amount),
        "date": settlement.date,
        "notes": settlement.notes,
    }


def snapshot(session: Session) -> dict:
    group = session.scalar(select(GroupRecord).order_by(GroupRecord.id))
    if group is None:
        raise RuntimeError("The database has not been initialized.")
    return {
        "group": {"id": group.id, "name": group.name, "closed": group.closed},
        "members": [member_dict(member) for member in session.scalars(select(MemberRecord).order_by(MemberRecord.id))],
        "expenses": [expense_dict(expense) for expense in session.scalars(select(ExpenseRecord).order_by(ExpenseRecord.id))],
        "settlements": [
            settlement_dict(settlement)
            for settlement in session.scalars(select(SettlementRecord).order_by(SettlementRecord.id))
        ],
    }


def reset_database() -> None:
    Base.metadata.drop_all(database_engine)
    Base.metadata.create_all(database_engine)
    with SessionLocal.begin() as session:
        session.add(GroupRecord(id="g1", name="Trip", closed=False))
        session.add_all([
            MemberRecord(id="m1", name="Alice"),
            MemberRecord(id="m2", name="Bob"),
        ])


Base.metadata.create_all(database_engine)
with SessionLocal() as initialization_session:
    if initialization_session.scalar(select(GroupRecord).limit(1)) is None:
        reset_database()
