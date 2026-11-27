"""Guest profile store: guests, their stay dates and confirmed allergies."""
import json
import sqlite3
from datetime import date

from app.models import Guest


class GuestRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, guest_id: int) -> Guest | None:
        row = self.conn.execute("SELECT * FROM guests WHERE id = ?", (guest_id,)).fetchone()
        return self._to_guest(row) if row else None

    def find(self, name: str, room: str) -> Guest | None:
        """Find a guest by surname and room (case-insensitive)."""
        row = self.conn.execute(
            "SELECT * FROM guests WHERE lower(name) = lower(?) AND room = ? ORDER BY id DESC",
            (name.strip(), str(room).strip()),
        ).fetchone()
        return self._to_guest(row) if row else None

    def save(self, guest: Guest) -> Guest:
        """Insert a new guest, or update an existing one. Returns the guest with its id."""
        values = (guest.name, guest.room, guest.stay_start.isoformat(),
                  guest.stay_end.isoformat(), json.dumps(sorted(set(guest.allergies))))
        if guest.guest_id is None:
            cur = self.conn.execute(
                "INSERT INTO guests (name, room, stay_start, stay_end, allergies) VALUES (?, ?, ?, ?, ?)",
                values)
            guest.guest_id = cur.lastrowid
        else:
            self.conn.execute(
                "UPDATE guests SET name = ?, room = ?, stay_start = ?, stay_end = ?, allergies = ? "
                "WHERE id = ?", values + (guest.guest_id,))
        self.conn.commit()
        return guest

    def add_allergies(self, guest_id: int, codes: list[str]) -> None:
        guest = self.get(guest_id)
        if guest is None:
            raise ValueError(f"No guest with id {guest_id}")
        guest.allergies = sorted(set(guest.allergies) | set(codes))
        self.save(guest)

    @staticmethod
    def _to_guest(row: sqlite3.Row) -> Guest:
        return Guest(name=row["name"], room=row["room"],
                     stay_start=date.fromisoformat(row["stay_start"]),
                     stay_end=date.fromisoformat(row["stay_end"]),
                     allergies=json.loads(row["allergies"]), guest_id=row["id"])