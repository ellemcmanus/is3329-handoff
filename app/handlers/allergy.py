"""Allergy and dietary handler: the most safety-critical request type."""
from app import allergens
from app.handlers.base import RequestHandler
from app.models import INFO, WARNING, ExtractedRequest, Flag, Guest, HandoffItem


class AllergyHandler(RequestHandler):
    def validate(self, request: ExtractedRequest, guest: Guest) -> HandoffItem:
        details = dict(request.details)
        details.setdefault("kind", "allergy")
        details.setdefault("allergens", [])
        flags: list[Flag] = []
        text = request.source_text.lower()

        if details["kind"] == "preference":
            flags.append(Flag(INFO, f"Preference, not an allergy: {details.get('avoid', 'see note')}."))
        elif not details["allergens"]:
            flags.append(Flag(WARNING, "Allergy mentioned but no allergen identified. Check the note."))

        for code in details["allergens"]:
            if code in allergens.AMBIGUOUS:
                name, question = allergens.AMBIGUOUS[code]
                flags.append(Flag(WARNING, f"{name}. {question}"))
            elif code not in allergens.EU_ALLERGENS:
                flags.append(Flag(WARNING, f"'{code}' is not one of the 14 regulated allergens. Check the note."))

        # Wording that hides whether this is medical or a preference.
        if "gluten-free" in text or "gluten free" in text:
            if "coeliac" not in text and "celiac" not in text:
                flags.append(Flag(WARNING, "Gluten-free: ask whether this is coeliac (medical) or a preference."))
        if "dairy-free" in text or "dairy free" in text:
            flags.append(Flag(WARNING, "Dairy-free: ask whether this is a milk allergy or lactose intolerance."))

        if details.get("severity") == "severe":
            flags.append(Flag(INFO, "Severe allergy: highlight on the kitchen briefing."))

        return HandoffItem(request.request_type, details, request.source_text, flags)