"""Real LLM extractor: to be completed in Deliverable 3.

It implements the same RequestExtractor interface as the mock, so nothing
else in the application changes when it is switched on (EXTRACTOR=llm).

Plan for D3:
  1. Remove guest names and room numbers from the note (privacy risk).
  2. Send the note to the LLM API with a fixed instruction and ask for JSON
     matching the ExtractedRequest fields (temperature 0, pinned model).
  3. Treat the note as data, never as instructions (prompt-injection risk).
  4. Use a timeout; on timeout, error or malformed JSON raise ExtractorError
     so the app falls back to manual entry.
"""
from app.extractor.base import ExtractorError, RequestExtractor
from app.models import ExtractedRequest


class LLMExtractor(RequestExtractor):
    def __init__(self, api_key: str | None, model: str, timeout_seconds: float = 10):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def extract(self, note_text: str) -> list[ExtractedRequest]:
        raise ExtractorError("The real LLM extractor is not implemented yet (planned for D3).")
