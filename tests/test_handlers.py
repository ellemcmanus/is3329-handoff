from conftest import TODAY

from app.handlers import create_handlers
from app.models import ALLERGY, CELEBRATION, COMPLAINT, INFO, PICNIC, WARNING, ExtractedRequest

handlers = create_handlers(TODAY)


def warnings(item):
    return [f.message for f in item.flags if f.level == WARNING]


def test_valid_allergy_has_no_warnings(guest):
    req = ExtractedRequest(ALLERGY, {"allergens": ["celery"], "kind": "allergy"}, "allergic to celery")
    assert warnings(handlers[ALLERGY].validate(req, guest)) == []


def test_ambiguous_nuts_asks_which_nuts(guest):
    req = ExtractedRequest(ALLERGY, {"allergens": ["nuts_unspecified"]}, "allergic to nuts")
    assert any("peanuts, tree nuts" in w for w in warnings(handlers[ALLERGY].validate(req, guest)))


def test_gluten_free_without_coeliac_asks_if_medical(guest):
    req = ExtractedRequest(ALLERGY, {"allergens": ["cereals_gluten"]}, "she eats gluten-free")
    assert any("coeliac" in w for w in warnings(handlers[ALLERGY].validate(req, guest)))


def test_preference_is_labelled_not_an_allergy(guest):
    req = ExtractedRequest(ALLERGY, {"allergens": [], "kind": "preference", "avoid": "onion"}, "prefers no onion")
    item = handlers[ALLERGY].validate(req, guest)
    assert any(f.level == INFO and "Preference" in f.message for f in item.flags)
    assert warnings(item) == []


def test_valid_picnic_passes(guest):
    req = ExtractedRequest(PICNIC, {"people": 2, "date": "2026-12-03", "pickup_time": "12:00"}, "")
    assert warnings(handlers[PICNIC].validate(req, guest)) == []


def test_picnic_outside_stay_is_flagged(guest):
    req = ExtractedRequest(PICNIC, {"people": 4, "date": "2026-12-06", "pickup_time": "13:00"}, "")
    assert any("outside the guest's stay" in w for w in warnings(handlers[PICNIC].validate(req, guest)))


def test_picnic_in_the_past_is_flagged(guest):
    req = ExtractedRequest(PICNIC, {"people": 2, "date": "2026-12-01", "pickup_time": "12:00"}, "")
    assert any("in the past" in w for w in warnings(handlers[PICNIC].validate(req, guest)))


def test_picnic_missing_pickup_time_is_flagged(guest):
    req = ExtractedRequest(PICNIC, {"people": 2, "date": "2026-12-03"}, "")
    assert any("pickup time" in w for w in warnings(handlers[PICNIC].validate(req, guest)))


def test_celebration_without_date_is_flagged(guest):
    req = ExtractedRequest(CELEBRATION, {"occasion": "birthday", "request": "cake"}, "")
    assert any("no date" in w for w in warnings(handlers[CELEBRATION].validate(req, guest)))


def test_unreadable_date_is_flagged_not_crashed(guest):
    req = ExtractedRequest(CELEBRATION, {"occasion": "birthday", "request": "cake", "date": "next Fri"}, "")
    assert any("could not be read" in w for w in warnings(handlers[CELEBRATION].validate(req, guest)))


def test_complaint_without_issue_is_flagged(guest):
    req = ExtractedRequest(COMPLAINT, {"about": "soup"}, "")
    assert warnings(handlers[COMPLAINT].validate(req, guest))