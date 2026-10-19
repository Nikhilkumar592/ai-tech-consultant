"""Tests for the 20-consecutive-approval autonomy transition rule."""
import pytest
import pytest_asyncio
from app.database import init_db
from app.autonomy import (
    record_approval,
    record_rejection,
    record_edit,
    toggle_autonomy,
    get_all_autonomy_statuses,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_twenty_consecutive_approval_rule():
    cat = "general_inquiry"

    # Reset any existing streak and autonomy state
    await record_rejection(cat)
    await toggle_autonomy(cat, enable=False)

    # Approve 19 times -> suggestion_ready should remain False
    for i in range(19):
        res = await record_approval(cat)
        assert res["consecutive_approvals"] == i + 1
        assert res["suggestion_ready"] is False

    # 20th approval -> suggestion_ready should become True!
    res_20 = await record_approval(cat)
    assert res_20["consecutive_approvals"] == 20
    assert res_20["suggestion_ready"] is True
    assert res_20["is_autonomous"] is False  # Not autonomous until human confirms!

    # Human confirms transition
    toggle_res = await toggle_autonomy(cat, enable=True, confirmed_by="Engineering Lead")
    assert toggle_res["is_autonomous"] is True


@pytest.mark.asyncio
async def test_rejection_resets_streak():
    cat = "billing"

    # Build streak to 5
    for _ in range(5):
        await record_approval(cat)

    # Rejection resets streak
    res = await record_rejection(cat)
    assert res["consecutive_approvals"] == 0


@pytest.mark.asyncio
async def test_autonomy_statuses():
    statuses = await get_all_autonomy_statuses()
    assert len(statuses) >= 4
    categories = [s["category"] for s in statuses]
    assert "technical_support" in categories
    assert "billing" in categories
