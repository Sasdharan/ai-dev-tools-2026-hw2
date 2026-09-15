from datetime import date
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import (
    ExpenseRecord,
    GroupRecord,
    MemberRecord,
    SettlementRecord,
    expense_dict,
    get_session,
    next_id,
    settlement_dict,
    snapshot,
)
from .schemas import (
    AddExpenseRequest,
    AddMemberRequest,
    AppState,
    ErrorResponse,
    Expense,
    Group,
    Member,
    RecordSettlementRequest,
    Settlement,
)

app = FastAPI(
    title="CloseTab MVP API",
    version="1.0.0",
    description="Database-backed API for the CloseTab MVP frontend.",
)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    del request
    for error in exc.errors():
        if error.get("loc") == ("body", "name") and error.get("type") == "value_error":
            return JSONResponse(
                status_code=400,
                content={"detail": "Member name must not be blank."},
            )
    return JSONResponse(status_code=400, content={"detail": "Invalid request."})


def _group(session: Session) -> GroupRecord:
    group = session.scalar(select(GroupRecord).order_by(GroupRecord.id))
    if group is None:
        raise HTTPException(status_code=500, detail="Group is not initialized.")
    return group


def _balances(session: Session) -> dict[str, float]:
    members = session.scalars(select(MemberRecord).order_by(MemberRecord.id)).all()
    expenses = session.scalars(select(ExpenseRecord).order_by(ExpenseRecord.id)).all()
    settlements = session.scalars(select(SettlementRecord).order_by(SettlementRecord.id)).all()
    balances = {member.id: 0.0 for member in members}

    for expense in expenses:
        share = float(expense.amount) / len(expense.participants)
        for participant in expense.participants:
            balances[participant.id] -= share
        balances[expense.payer_id] += float(expense.amount)

    for settlement in settlements:
        balances[settlement.from_id] += float(settlement.amount)
        balances[settlement.to_id] -= float(settlement.amount)

    return balances


@app.get("/state", response_model=AppState, tags=["Group"], operation_id="fetchState")
def fetch_state(session: Session = Depends(get_session)) -> dict[str, Any]:
    return snapshot(session)


@app.post(
    "/members",
    response_model=Member,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    tags=["Members"],
    operation_id="addMember",
)
def add_member(
    request: AddMemberRequest, session: Session = Depends(get_session)
) -> dict[str, str]:
    member = MemberRecord(id=next_id(session, MemberRecord, "m"), name=request.name)
    session.add(member)
    session.commit()
    return {"id": member.id, "name": member.name}


@app.post(
    "/expenses",
    response_model=Expense,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    tags=["Expenses"],
    operation_id="addExpense",
)
def add_expense(
    request: AddExpenseRequest, session: Session = Depends(get_session)
) -> dict[str, Any]:
    group = _group(session)
    if group.closed:
        raise HTTPException(status_code=409, detail="Group is closed.")
    if request.date > date.today():
        raise HTTPException(status_code=400, detail="Expense date cannot be in the future.")

    member_ids = set(session.scalars(select(MemberRecord.id)).all())
    if not set(request.participants).issubset(member_ids) or request.payer not in member_ids:
        raise HTTPException(
            status_code=409,
            detail="All participants and the payer must be valid members.",
        )
    if len(set(request.participants)) != len(request.participants):
        raise HTTPException(status_code=400, detail="Participants must be unique.")

    participants = session.scalars(
        select(MemberRecord).where(MemberRecord.id.in_(request.participants))
    ).all()
    expense = ExpenseRecord(
        id=next_id(session, ExpenseRecord, "e"),
        desc=request.desc,
        amount=request.amount,
        date=request.date,
        payer_id=request.payer,
        locked=False,
        participants=participants,
    )
    session.add(expense)
    session.commit()
    return expense_dict(expense)


@app.post(
    "/settlements",
    response_model=Settlement,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    tags=["Settlements"],
    operation_id="recordSettlement",
)
def record_settlement(
    request: RecordSettlementRequest, session: Session = Depends(get_session)
) -> dict[str, Any]:
    group = _group(session)
    if not group.closed:
        raise HTTPException(
            status_code=409,
            detail="Group must be closed before recording settlements.",
        )

    member_ids = set(session.scalars(select(MemberRecord.id)).all())
    if request.from_ not in member_ids or request.to not in member_ids:
        raise HTTPException(
            status_code=409,
            detail="Settlement members must be valid members.",
        )

    settlement = SettlementRecord(
        id=next_id(session, SettlementRecord, "s"),
        from_id=request.from_,
        to_id=request.to,
        amount=request.amount,
        date=request.date,
        notes=request.notes,
    )
    session.add(settlement)
    session.commit()
    return settlement_dict(settlement)


@app.post(
    "/group/close",
    response_model=Group,
    responses={409: {"model": ErrorResponse}},
    tags=["Group"],
    operation_id="closeGroup",
)
def close_group(session: Session = Depends(get_session)) -> dict[str, Any]:
    group = _group(session)
    if group.closed:
        raise HTTPException(status_code=409, detail="Group is already closed.")
    group.closed = True
    session.commit()
    return {"id": group.id, "name": group.name, "closed": group.closed}


@app.post(
    "/group/reopen",
    response_model=Group,
    responses={409: {"model": ErrorResponse}},
    tags=["Group"],
    operation_id="reopenGroup",
)
def reopen_group(session: Session = Depends(get_session)) -> dict[str, Any]:
    group = _group(session)
    if not group.closed:
        raise HTTPException(status_code=409, detail="Group is already open.")
    group.closed = False
    session.commit()
    return {"id": group.id, "name": group.name, "closed": group.closed}


@app.get(
    "/balances",
    response_model=dict[str, float],
    tags=["Balances"],
    operation_id="computeBalances",
)
def compute_balances(session: Session = Depends(get_session)) -> dict[str, float]:
    return _balances(session)


frontend_directory = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
