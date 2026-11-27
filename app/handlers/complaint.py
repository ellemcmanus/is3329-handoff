"""Food complaint handler.

Escalation of complaints that suggest an allergic reaction is done by the
safety rules engine, not here, so that all safety logic lives in one place.
"""
from app.handlers.base import RequestHandler
from app.models import WARNING, ExtractedRequest, Flag, Guest, HandoffItem


class ComplaintHandler(RequestHandler):
    def validate(self, request: ExtractedRequest, guest: Guest) -> HandoffItem:
        details = dict(request.details)
        flags: list[Flag] = []
        if not details.get("issue"):
            flags.append(Flag(WARNING, "Complaint without a clear issue. Check the original note."))
        return HandoffItem(request.request_type, details, request.source_text, flags)