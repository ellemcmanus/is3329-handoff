"""Celebration handler: birthdays, anniversaries and other occasions."""
from app.handlers.base import RequestHandler
from app.models import WARNING, ExtractedRequest, Flag, Guest, HandoffItem


class CelebrationHandler(RequestHandler):
    def validate(self, request: ExtractedRequest, guest: Guest) -> HandoffItem:
        details = dict(request.details)
        flags: list[Flag] = self.check_date(details.get("date"), guest, "Celebration")

        if not details.get("occasion"):
            flags.append(Flag(WARNING, "Occasion not stated (birthday, anniversary...)."))
        if not details.get("request"):
            flags.append(Flag(WARNING, "No request stated (cake, message, candle...). Ask the guest."))

        return HandoffItem(request.request_type, details, request.source_text, flags)