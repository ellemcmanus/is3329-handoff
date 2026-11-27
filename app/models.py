"""Shared data shapes used by every component.

Keeping them in one place means all components "speak the same language"
and no component needs to know how another one stores its data.
"""
from dataclasses import dataclass, field
from datetime import date

# The four request types the system understands.
ALLERGY = "allergy"
CELEBRATION = "celebration"
COMPLAINT = "complaint"
PICNIC = "picnic"
REQUEST_TYPES = (ALLERGY, CELEBRATION, COMPLAINT, PICNIC)

# Flag levels, from least to most serious.
INFO = "info"          # useful to know
WARNING = "warning"    # reception should check or ask the guest
URGENT = "urgent"      # kitchen and manager must know straight away
BLOCK = "block"        # cannot be confirmed until a human has checked it


@dataclass
class Guest:
    name: str
    room: str
    stay_start: date
    stay_end: date
    allergies: list[str] = field(default_factory=list)  # EU allergen codes
    guest_id: int | None = None

    def is_staying_on(self, day: date) -> bool:
        return self.stay_start <= day <= self.stay_end


@dataclass
class ExtractedRequest:
    """One request found in a guest note by the AI extractor."""
    request_type: str
    details: dict
    source_text: str  # the part of the note this request came from


@dataclass
class Flag:
    level: str
    message: str
    item_index: int | None = None  # which request it belongs to; None = whole note


@dataclass
class HandoffItem:
    """A validated request, ready for reception to review and confirm."""
    request_type: str
    details: dict
    source_text: str
    flags: list[Flag] = field(default_factory=list)
    item_id: int | None = None
    note_id: int | None = None
    confirmed_by: str | None = None
    confirmed_at: str | None = None

    @property
    def is_blocked(self) -> bool:
        return any(f.level == BLOCK for f in self.flags)

    @property
    def is_confirmed(self) -> bool:
        return self.confirmed_by is not None


@dataclass
class Booking:
    guest_name: str
    room: str
    day: date
    service: str  # "lunch" or "dinner"
    time: str     # "19:00"
    table: str
    party_size: int


@dataclass
class BriefingRow:
    booking: Booking
    allergies: list[str]
    requests: list[HandoffItem]
    urgent: bool = False


@dataclass
class Briefing:
    day: date
    service: str
    rows: list[BriefingRow]
    picnics: list[HandoffItem] = field(default_factory=list)
