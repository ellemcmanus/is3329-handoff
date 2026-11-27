"""Intake gateway: receives a guest note and passes it through the pipeline.

Target design: the note becomes a NoteReceived event on an event bus, and
each step below is a separate consumer working in the background.
Prototype (Simplified): the steps are direct function calls, one after the
other. Each step still goes through its component's interface, so moving
to an event bus later changes this file only.
"""
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime

from app.bookings import BookingProvider
from app.extractor import ExtractorError, RequestExtractor
from app.guests import GuestRepository
from app.handlers.base import RequestHandler
from app.models import (BLOCK, CELEBRATION, INFO, WARNING, Flag, Guest, HandoffItem)
from app.review import ReviewService
from app.safety import SafetyChecker


@dataclass
class GuestNote:
    guest_name: str
    room: str
    stay_start: date
    stay_end: date
    text: str


@dataclass
class NoteRecord:
    note_id: int
    guest: Guest
    text: str
    created_at: str
    ai_failed: bool
    flags: list[Flag]


class IntakeService:
    def __init__(self, conn: sqlite3.Connection, extractor: RequestExtractor,
                 handlers: dict[str, RequestHandler], safety: SafetyChecker,
                 guests: GuestRepository, bookings: BookingProvider, review: ReviewService):
        self.conn = conn
        self.extractor = extractor
        self.handlers = handlers
        self.safety = safety
        self.guests = guests
        self.bookings = bookings
        self.review = review

    def submit_note(self, note: GuestNote) -> int:
        """Save the note, process it, and return its id for the review screen."""
        guest = self._find_or_create_guest(note)
        note_flags: list[Flag] = []
        ai_failed = False

        # 1. AI extraction (the slow step that can fail).
        try:
            extracted = self.extractor.extract(note.text)
        except ExtractorError as e:
            extracted, ai_failed = [], True
            note_flags.append(Flag(WARNING, f"AI unavailable ({e}). Enter the requests manually."))

        if not extracted and not ai_failed:
            note_flags.append(Flag(INFO, "No kitchen requests found in this note."))

        # 2. Validate each request with the handler for its type.
        items: list[HandoffItem] = []
        for request in extracted:
            items.append(self.handlers[request.request_type].validate(request, guest))

        # 3. Link celebrations to the guest's restaurant booking.
        for item in items:
            if item.request_type == CELEBRATION:
                item.flags += self._link_booking(item, guest)

        # 4. Safety rules on the raw note and the AI output (runs even if the AI failed).
        for flag in self.safety.check(note.text, items, guest):
            if flag.item_index is None:
                note_flags.append(flag)
            else:
                items[flag.item_index].flags.append(flag)

        # A note-level block (e.g. a missed allergen) blocks every request from that note.
        blocks = [f for f in note_flags if f.level == BLOCK]
        for item in items:
            item.flags += [Flag(f.level, f.message) for f in blocks]

        # 5. Save the note and the pending requests for review.
        note_id = self._save_note(guest, note.text, ai_failed, note_flags)
        self.review.save_pending(note_id, guest.guest_id, items)
        return note_id

    def get_note(self, note_id: int) -> NoteRecord | None:
        row = self.conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            return None
        return NoteRecord(note_id=row["id"], guest=self.guests.get(row["guest_id"]),
                          text=row["note_text"], created_at=row["created_at"],
                          ai_failed=bool(row["ai_failed"]),
                          flags=[Flag(**f) for f in json.loads(row["flags"])])

    # Steps ---------------------------------------------------------------

    def _find_or_create_guest(self, note: GuestNote) -> Guest:
        guest = self.guests.find(note.guest_name, note.room)
        if guest is None:
            guest = Guest(note.guest_name.strip(), str(note.room).strip(), note.stay_start, note.stay_end)
        else:
            guest.stay_start, guest.stay_end = note.stay_start, note.stay_end
        return self.guests.save(guest)

    def _link_booking(self, item: HandoffItem, guest: Guest) -> list[Flag]:
        day = RequestHandler.parse_date(item.details.get("date"))
        if day is None:
            return []
        bookings = self.bookings.get_bookings(guest, day)
        service = item.details.get("service")
        if service:
            bookings = [b for b in bookings if b.service == service]
        if not bookings:
            return [Flag(WARNING, f"No restaurant booking found for {guest.name} on {day:%a %d %b}.")]
        if len(bookings) > 1:
            options = ", ".join(f"{b.service} {b.time}" for b in bookings)
            return [Flag(WARNING, f"{guest.name} has {len(bookings)} bookings that day ({options}). "
                                  f"Confirm which meal.")]
        b = bookings[0]
        item.details["booking"] = f"{b.day:%a %d %b}, {b.service} {b.time}, table {b.table}"
        return []

    def _save_note(self, guest: Guest, text: str, ai_failed: bool, flags: list[Flag]) -> int:
        cur = self.conn.execute(
            "INSERT INTO notes (guest_id, note_text, created_at, ai_failed, flags) VALUES (?, ?, ?, ?, ?)",
            (guest.guest_id, text, datetime.now().isoformat(timespec="minutes"), int(ai_failed),
             json.dumps([asdict(f) for f in flags])))
        self.conn.commit()
        return cur.lastrowid