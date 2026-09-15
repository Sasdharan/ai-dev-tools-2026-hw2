from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import database
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
    description="In-memory backend for the CloseTab MVP frontend.",
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


def _member_ids() -> set[str]:
    return {member["id"] for member in database.members}


def _balances() -> dict[str, float]:
    balances = {member["id"]: 0.0 for member in database.members}

    for expense in database.expenses:
        share = expense["amount"] / len(expense["participants"])
        for participant in expense["participants"]:
            balances[participant] -= share
        balances[expense["payer"]] += expense["amount"]

    for settlement in database.settlements:
        balances[settlement["from"]] += settlement["amount"]
        balances[settlement["to"]] -= settlement["amount"]

    return balances


@app.get("/state", response_model=AppState, tags=["Group"], operation_id="fetchState")
def fetch_state() -> dict[str, Any]:
    return database.snapshot()


@app.post(
    "/members",
    response_model=Member,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    tags=["Members"],
    operation_id="addMember",
)
def add_member(request: AddMemberRequest) -> dict[str, str]:
    member = {"id": database.new_member_id(), "name": request.name}
    database.members.append(member)
    return member


@app.post(
    "/expenses",
    response_model=Expense,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    tags=["Expenses"],
    operation_id="addExpense",
)
def add_expense(request: AddExpenseRequest) -> dict[str, Any]:
    if database.group["closed"]:
        raise HTTPException(status_code=409, detail="Group is closed.")
    if request.date > date.today():
        raise HTTPException(status_code=400, detail="Expense date cannot be in the future.")

    member_ids = _member_ids()
    if not set(request.participants).issubset(member_ids) or request.payer not in member_ids:
        raise HTTPException(
            status_code=409,
            detail="All participants and the payer must be valid members.",
        )

    expense = {
        "id": database.new_expense_id(),
        "desc": request.desc,
        "amount": request.amount,
        "date": request.date,
        "participants": request.participants,
        "payer": request.payer,
        "locked": False,
    }
    database.expenses.append(expense)
    return expense


@app.post(
    "/settlements",
    response_model=Settlement,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    tags=["Settlements"],
    operation_id="recordSettlement",
)
def record_settlement(request: RecordSettlementRequest) -> dict[str, Any]:
    if not database.group["closed"]:
        raise HTTPException(
            status_code=409,
            detail="Group must be closed before recording settlements.",
        )

    member_ids = _member_ids()
    if request.from_ not in member_ids or request.to not in member_ids:
        raise HTTPException(
            status_code=409,
            detail="Settlement members must be valid members.",
        )

    settlement = {
        "id": database.new_settlement_id(),
        "from": request.from_,
        "to": request.to,
        "amount": request.amount,
        "date": request.date,
        "notes": request.notes,
    }
    database.settlements.append(settlement)
    return settlement


@app.post(
    "/group/close",
    response_model=Group,
    responses={409: {"model": ErrorResponse}},
    tags=["Group"],
    operation_id="closeGroup",
)
def close_group() -> dict[str, Any]:
    if database.group["closed"]:
        raise HTTPException(status_code=409, detail="Group is already closed.")
    database.group["closed"] = True
    return database.group


@app.post(
    "/group/reopen",
    response_model=Group,
    responses={409: {"model": ErrorResponse}},
    tags=["Group"],
    operation_id="reopenGroup",
)
def reopen_group() -> dict[str, Any]:
    if not database.group["closed"]:
        raise HTTPException(status_code=409, detail="Group is already open.")
    database.group["closed"] = False
    return database.group


@app.get(
    "/balances",
    response_model=dict[str, float],
    tags=["Balances"],
    operation_id="computeBalances",
)
def compute_balances() -> dict[str, float]:
    return _balances()


frontend_directory = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
