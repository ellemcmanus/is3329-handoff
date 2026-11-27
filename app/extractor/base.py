"""Request extractor (AI) interface.

The rest of the application only ever uses this class. Whether the
requests come from a real LLM or from the mock is decided once, in
app/config.py, so swapping them is a one-line change.
"""
from abc import ABC, abstractmethod

from app.models import ExtractedRequest


class ExtractorError(Exception):
    """Raised when the AI cannot be reached or returns unusable output.

    The intake service catches this and falls back to manual entry,
    so an AI failure never crashes the app.
    """


class RequestExtractor(ABC):
    @abstractmethod
    def extract(self, note_text: str) -> list[ExtractedRequest]:
        """Split a free-text guest note into individual, classified requests.

        Returns an empty list when the note contains nothing for the kitchen.
        Raises ExtractorError when the AI fails.
        """
