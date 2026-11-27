"""Shared test set-up (part 1). Part 2 is added in step 9."""
from datetime import date

import pytest

from app.models import Guest

TODAY = date(2026, 12, 2)  # fixed "today" so tests never go stale
STAY_START, STAY_END = date(2026, 12, 2), date(2026, 12, 5)


@pytest.fixture
def guest():
    return Guest("Murphy", "3", STAY_START, STAY_END, guest_id=1)