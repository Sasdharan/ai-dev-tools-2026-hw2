from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.main import app
from app.database import Base, database_engine, reset_database


@pytest.fixture(autouse=True)
def clean_database():
    reset_database()


@pytest.fixture
def client():
    return TestClient(app)


def test_root_serves_frontend(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "CloseTab MVP" in response.text


def test_get_state_returns_seeded_group(client):
    response = client.get("/state")

    assert response.status_code == 200
    assert response.json() == {
        "group": {"id": "g1", "name": "Trip", "closed": False},
        "members": [
            {"id": "m1", "name": "Alice"},
            {"id": "m2", "name": "Bob"},
        ],
        "expenses": [],
        "settlements": [],
    }


def test_database_schema_is_persistent_sqlalchemy_schema():
    tables = set(inspect(database_engine).get_table_names())

    assert set(Base.metadata.tables) <= tables


def test_member_persists_across_client_instances(client):
    response = client.post("/members", json={"name": "Charlie"})
    assert response.status_code == 201

    second_client = TestClient(app)
    state = second_client.get("/state")

    assert state.status_code == 200
    assert {member["name"] for member in state.json()["members"]} == {
        "Alice",
        "Bob",
        "Charlie",
    }


def test_add_member_returns_created_member(client):
    response = client.post("/members", json={"name": "Charlie"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Charlie"
    assert body["id"].startswith("m")

    state = client.get("/state").json()
    assert body in state["members"]


def test_add_member_rejects_blank_name(client):
    response = client.post("/members", json={"name": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Member name must not be blank."


def test_add_expense_returns_expense_and_updates_balances(client):
    response = client.post(
        "/expenses",
        json={
            "desc": "Dinner",
            "amount": 60,
            "date": "2026-09-15",
            "participants": ["m1", "m2"],
            "payer": "m1",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "desc": "Dinner",
        "amount": 60.0,
        "date": "2026-09-15",
        "participants": ["m1", "m2"],
        "payer": "m1",
        "locked": False,
    }
    assert client.get("/balances").json() == {"m1": 30.0, "m2": -30.0}


def test_add_expense_rejects_unknown_participant(client):
    response = client.post(
        "/expenses",
        json={
            "desc": "Dinner",
            "amount": 60,
            "date": "2026-09-15",
            "participants": ["m1", "unknown"],
            "payer": "m1",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "All participants and the payer must be valid members."


def test_add_expense_rejects_future_date(client):
    future = (date.today() + timedelta(days=1)).isoformat()
    response = client.post(
        "/expenses",
        json={
            "desc": "Dinner",
            "amount": 60,
            "date": future,
            "participants": ["m1"],
            "payer": "m1",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Expense date cannot be in the future."


def test_group_close_blocks_expenses_and_reopen_allows_them(client):
    assert client.post("/group/close").json()["closed"] is True

    blocked = client.post(
        "/expenses",
        json={
            "desc": "Dinner",
            "amount": 60,
            "date": "2026-09-15",
            "participants": ["m1"],
            "payer": "m1",
        },
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "Group is closed."

    assert client.post("/group/reopen").json()["closed"] is False
    assert client.post(
        "/expenses",
        json={
            "desc": "Dinner",
            "amount": 60,
            "date": "2026-09-15",
            "participants": ["m1"],
            "payer": "m1",
        },
    ).status_code == 201


def test_settlement_requires_closed_group_and_updates_balances(client):
    client.post(
        "/expenses",
        json={
            "desc": "Dinner",
            "amount": 60,
            "date": "2026-09-15",
            "participants": ["m1", "m2"],
            "payer": "m1",
        },
    )

    open_response = client.post(
        "/settlements",
        json={"from": "m2", "to": "m1", "amount": 30, "date": "2026-09-15"},
    )
    assert open_response.status_code == 409
    assert open_response.json()["detail"] == "Group must be closed before recording settlements."

    client.post("/group/close")
    response = client.post(
        "/settlements",
        json={
            "from": "m2",
            "to": "m1",
            "amount": 30,
            "date": "2026-09-15",
            "notes": "Cash payment",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "from": "m2",
        "to": "m1",
        "amount": 30.0,
        "date": "2026-09-15",
        "notes": "Cash payment",
    }
    assert client.get("/balances").json() == {"m1": 0.0, "m2": 0.0}


def test_close_and_reopen_are_idempotency_errors(client):
    assert client.post("/group/close").status_code == 200
    assert client.post("/group/close").status_code == 409
    assert client.post("/group/reopen").status_code == 200
    assert client.post("/group/reopen").status_code == 409
