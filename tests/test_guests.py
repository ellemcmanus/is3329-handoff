from conftest import STAY_END, STAY_START

from app import db
from app.guests import GuestRepository
from app.models import Guest


def test_save_then_find_guest():
    repo = GuestRepository(db.connect(":memory:"))
    saved = repo.save(Guest("Murphy", "3", STAY_START, STAY_END))
    found = repo.find("murphy", "3")
    assert found.guest_id == saved.guest_id and found.stay_end == STAY_END


def test_add_allergies_does_not_duplicate():
    repo = GuestRepository(db.connect(":memory:"))
    g = repo.save(Guest("Nolan", "5", STAY_START, STAY_END))
    repo.add_allergies(g.guest_id, ["celery"])
    repo.add_allergies(g.guest_id, ["celery", "mustard"])
    assert repo.get(g.guest_id).allergies == ["celery", "mustard"]