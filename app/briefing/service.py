"""Briefing service: the written kitchen briefing that replaces the verbal hand-off.

One row per restaurant booking for a service, ordered by seating time, with
the guest's allergies first and their confirmed requests beside them.
Only CONFIRMED requests appear.
"""
from datetime import date

from app import allergens
from app.bookings import BookingProvider
from app.guests import GuestRepository
from app.handlers.base import RequestHandler
from app.models import (ALLERGY, CELEBRATION, COMPLAINT, PICNIC, URGENT, Briefing, BriefingRow,
                        HandoffItem)
from app.review import ReviewService


class BriefingService:
    def __init__(self, bookings: BookingProvider, guests: GuestRepository, review: ReviewService):
        self.bookings = bookings
        self.guests = guests
        self.review = review

    def build(self, day: date, service: str) -> Briefing:
        rows = []
        for booking in self.bookings.get_service(day, service):  # already ordered by time
            guest = self.guests.find(booking.guest_name, booking.room)
            if guest is None:
                rows.append(BriefingRow(booking, [], []))
                continue
            confirmed = self.review.confirmed_for_guest(guest.guest_id)
            allergy_lines = self._allergy_lines(confirmed, guest.allergies)
            requests = [i for i in confirmed if self._belongs_to_meal(i, day, service)]
            urgent = any(f.level == URGENT for i in requests for f in i.flags)
            rows.append(BriefingRow(booking, allergy_lines, requests, urgent))

        picnics = [i for i in self.review.confirmed_of_type(PICNIC)
                   if RequestHandler.parse_date(i.details.get("date")) == day]
        return Briefing(day, service, rows, picnics)

    @staticmethod
    def _allergy_lines(confirmed: list[HandoffItem], profile_codes: list[str]) -> list[str]:
        lines, shown = [], set()
        for item in confirmed:
            if item.request_type != ALLERGY:
                continue
            codes = item.details.get("allergens", [])
            shown.update(codes)
            text = ", ".join(allergens.label(c) for c in codes) or item.details.get("avoid", "")
            extras = [x for x in (item.details.get("person"), item.details.get("severity")) if x]
            if item.details.get("kind") == "preference":
                extras.append("preference")
            lines.append(text + (f" ({', '.join(extras)})" if extras else ""))
        # Allergies already on the guest's profile from an earlier note.
        for code in profile_codes:
            if code not in shown:
                lines.append(allergens.label(code))
        return lines

    @staticmethod
    def _belongs_to_meal(item: HandoffItem, day: date, service: str) -> bool:
        if item.request_type == COMPLAINT:
            return True  # the kitchen should know before the guest's next meal
        if item.request_type == CELEBRATION:
            item_day = RequestHandler.parse_date(item.details.get("date"))
            return item_day == day and item.details.get("service", service) == service
        return False