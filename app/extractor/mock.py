"""Mock extractor: returns realistic, hard-coded results for the synthetic notes.

It lets the whole application and its tests run with no API key, no cost
and the same result every time. One note (the birthday cake with "no
walnuts") deliberately misses the allergen, so the safety net can be shown
catching an AI mistake.
"""
import json
from pathlib import Path

from app.extractor.base import ExtractorError, RequestExtractor
from app.models import REQUEST_TYPES, ExtractedRequest


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())


class MockExtractor(RequestExtractor):
    def __init__(self, notes_file: Path):
        with open(notes_file, encoding="utf-8") as f:
            notes = json.load(f)
        self._responses = {_normalise(n["note_text"]): n["mock_response"] for n in notes}

    def extract(self, note_text: str) -> list[ExtractedRequest]:
        if "simulate ai failure" in note_text.lower():
            raise ExtractorError("Simulated AI failure (timeout).")

        response = self._responses.get(_normalise(note_text))
        if response is None:
            # A note the mock has never seen: behave like an AI that found nothing.
            return []

        requests = []
        for r in response:
            if r["request_type"] not in REQUEST_TYPES:
                raise ExtractorError(f"Unknown request type: {r['request_type']}")
            requests.append(ExtractedRequest(r["request_type"], dict(r["details"]), r["source_text"]))
        return requests