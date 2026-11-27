"""Picnic order handler."""
from app.handlers.base import RequestHandler
from app.models import WARNING, ExtractedRequest, Flag, Guest, HandoffItem


class PicnicHandler(RequestHandler):
    def validate(self, request: ExtractedRequest, guest: Guest) -> HandoffItem:
        details = dict(request.details)
        flags: list[Flag] = self.check_date(details.get("date"), guest, "Picnic")

        if not details.get("pickup_time"):
            flags.append(Flag(WARNING, "Picnic pickup time missing. Ask the guest."))
        if not details.get("people"):
            flags.append(Flag(WARNING, "Number of people missing. Ask the guest."))

        return HandoffItem(request.request_type, details, request.source_text, flags)