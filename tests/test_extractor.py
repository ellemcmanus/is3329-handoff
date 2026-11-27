"""Tests for the extractor interface. They check STRUCTURE, not exact wording,
so the same tests can be run against the real LLM in D3."""
import pytest

from app.config import DATA_DIR
from app.extractor import ExtractorError, RequestExtractor
from app.extractor.mock import MockExtractor
from app.models import REQUEST_TYPES

extractor = MockExtractor(DATA_DIR / "synthetic_notes.json")
MURPHY = ("Anniversary is Friday, husband is coeliac, can we have a picnic midday on Thursday? "
          "Also the beef was tough last time we dined.")


def test_mock_implements_the_interface():
    assert isinstance(extractor, RequestExtractor)


def test_murphy_note_is_split_into_four_requests():
    requests = extractor.extract(MURPHY)
    assert sorted(r.request_type for r in requests) == ["allergy", "celebration", "complaint", "picnic"]


def test_every_request_has_a_known_type_and_its_source_text():
    for r in extractor.extract(MURPHY):
        assert r.request_type in REQUEST_TYPES
        assert r.source_text and r.source_text.lower() in MURPHY.lower()


def test_note_with_nothing_for_kitchen_returns_empty_list():
    assert extractor.extract("Can we have a late checkout on Saturday?") == []


def test_ai_failure_raises_extractor_error():
    with pytest.raises(ExtractorError):
        extractor.extract("Simulate AI failure. Guest is allergic to prawns.")