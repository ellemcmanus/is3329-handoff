"""Tests for the web pages, using Flask's built-in test client (no browser needed)."""
from datetime import date

import pytest

from app.config import Settings
from app.web import create_app

MURPHY = {"guest_name": "Murphy", "room": "3", "stay_start": "2026-12-02", "stay_end": "2026-12-05",
          "note_text": "Anniversary is Friday, husband is coeliac, can we have a picnic midday on Thursday? "
                       "Also the beef was tough last time we dined."}


@pytest.fixture
def client():
    app = create_app(Settings(database=":memory:", demo_today=date(2026, 12, 2)))
    return app.test_client()


def test_new_note_page_lists_the_synthetic_examples(client):
    page = client.get("/note")
    assert page.status_code == 200
    assert "Murphy, room 3" in page.get_data(as_text=True)


def test_incomplete_form_shows_a_message_instead_of_crashing(client):
    page = client.post("/note", data={"guest_name": "", "room": "3", "stay_start": "", "stay_end": "", "note_text": ""})
    assert page.status_code == 200
    assert "Fill in the guest name" in page.get_data(as_text=True)


def test_note_goes_to_review_page_with_four_requests(client):
    response = client.post("/note", data=MURPHY, follow_redirects=True)
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert page.count("Confirm request") == 4


def test_confirmed_allergy_appears_on_the_kitchen_briefing(client):
    client.post("/note", data=MURPHY)
    client.post("/review/item/1/confirm", data={"staff": "Aoife (reception)"})
    page = client.get("/briefing?date=2026-12-04&service=dinner").get_data(as_text=True)
    assert "Murphy" in page and "Cereals containing gluten" in page