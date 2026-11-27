"""Review and confirmation: nothing reaches the kitchen until a person confirms it."""
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime

from app.guests import GuestRepository
from app.models import ALLERGY, Flag, HandoffItem


class ConfirmationError(Exception):
    """Raised when a request cannot be confirmed yet."""


class ReviewService:
    def __init__(self, conn: sqlite3.Connection, guests: GuestRepository):
        self.conn = conn
        self.guests = guests

    def save_pending(self, note_id: int, guest_id: int, items: list[HandoffItem]) -> list[HandoffItem]:
        for item in items:
            cur = self.conn.execute(
                "INSERT INTO handoff_items (note_id, guest_id, request_type, details, source_text, flags) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (note_id, guest_id, item.request_type, json.dumps(item.details), item.source_text,
                 json.dumps([asdict(f) for f in item.flags])))
            item.item_id = cur.lastrowid
            item.note_id = note_id
        self.conn.commit()
        return items

    def items_for_note(self, note_id: int) -> list[HandoffItem]:
        rows = self.conn.execute("SELECT * FROM handoff_items WHERE note_id = ? ORDER BY id",
                                 (note_id,)).fetchall()
        return [self._to_item(r) for r in rows]

    def get_item(self, item_id: int) -> HandoffItem | None:
        row = self.conn.execute("SELECT * FROM handoff_items WHERE id = ?", (item_id,)).fetchone()
        return self._to_item(row) if row else None

    def confirm(self, item_id: int, staff_name: str, safety_checked: bool = False) -> HandoffItem:
        """Confirm one request. Blocked requests need an explicit safety check by staff."""
        item = self.get_item(item_id)
        if item is None:
            raise ConfirmationError("Request not found.")
        if not staff_name.strip():
            raise ConfirmationError("Pick your name before confirming.")
        if item.is_blocked and not safety_checked:
            raise ConfirmationError("This request has a safety-net warning. Read the original note, "
                                    "then tick 'I have checked the note' to confirm.")

        now = datetime.now().isoformat(timespec="minutes")
        self.conn.execute("UPDATE handoff_items SET confirmed_by = ?, confirmed_at = ? WHERE id = ?",
                          (staff_name.strip(), now, item_id))
        self.conn.commit()

        # A confirmed allergy is saved on the guest's profile, so it carries over
        # to their other requests and appears at every meal of their stay.
        row = self.conn.execute("SELECT guest_id FROM handoff_items WHERE id = ?", (item_id,)).fetchone()
        if item.request_type == ALLERGY and item.details.get("allergens"):
            self.guests.add_allergies(row["guest_id"], item.details["allergens"])
        return self.get_item(item_id)

    def confirmed_for_guest(self, guest_id: int) -> list[HandoffItem]:
        rows = self.conn.execute(
            "SELECT * FROM handoff_items WHERE guest_id = ? AND confirmed_by IS NOT NULL ORDER BY id",
            (guest_id,)).fetchall()
        return [self._to_item(r) for r in rows]

    def confirmed_of_type(self, request_type: str) -> list[HandoffItem]:
        rows = self.conn.execute(
            "SELECT * FROM handoff_items WHERE request_type = ? AND confirmed_by IS NOT NULL ORDER BY id",
            (request_type,)).fetchall()
        return [self._to_item(r) for r in rows]

    @staticmethod
    def _to_item(row: sqlite3.Row) -> HandoffItem:
        return HandoffItem(request_type=row["request_type"], details=json.loads(row["details"]),
                           source_text=row["source_text"],
                           flags=[Flag(**f) for f in json.loads(row["flags"])],
                           item_id=row["id"], note_id=row["note_id"],
                           confirmed_by=row["confirmed_by"], confirmed_at=row["confirmed_at"])