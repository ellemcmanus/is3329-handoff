"""Safety rules engine.

Plain rules that run on the ORIGINAL note text and on the AI's output.
They do not depend on the AI being right, so they still protect guests
when the AI misses something or is unavailable.

Rules:
  1. Allergen safety net: an allergen word in the note that is not covered
     by any extracted allergy (or the guest's profile) blocks confirmation.
  2. Allergy carry-over: a guest's allergies are attached to their
     celebration and picnic requests (e.g. a coeliac guest's cake).
  3. Complaint escalation: a complaint suggesting a reaction is urgent.
  4. Prompt-injection warning: text aimed at the AI is pointed out.
"""
import re

from app import allergens
from app.models import (ALLERGY, BLOCK, CELEBRATION, COMPLAINT, PICNIC, URGENT, WARNING,
                        Flag, Guest, HandoffItem)

REACTION_WORDS = ["unwell", "sick", "ill", "reaction", "rash", "swelling", "swollen", "hives",
                  "itchy", "anaphylaxis", "anaphylactic", "epipen", "epi-pen", "vomit", "vomiting",
                  "throat", "breathing"]

INJECTION_PHRASES = ["ignore previous", "ignore all previous", "ignore the above", "disregard",
                     "system prompt", "you are now", "new instructions"]


class SafetyChecker:
    def check(self, note_text: str, items: list[HandoffItem], guest: Guest) -> list[Flag]:
        flags: list[Flag] = []
        covered = self._covered_allergens(items, guest)
        flags += self._allergen_safety_net(note_text, covered)
        flags += self._carry_over_allergies(items, covered)
        flags += self._escalate_complaints(items)
        flags += self._injection_warning(note_text)
        return flags

    # Rule helpers ---------------------------------------------------------

    @staticmethod
    def _covered_allergens(items: list[HandoffItem], guest: Guest) -> set[str]:
        covered = set(guest.allergies)
        for item in items:
            if item.request_type == ALLERGY:
                covered.update(item.details.get("allergens", []))
        return covered

    @staticmethod
    def _is_covered(code: str, covered: set[str]) -> bool:
        if code in covered:
            return True
        if code == "nuts_unspecified":
            return bool({"peanuts", "tree_nuts"} & covered)
        if code == "shellfish_unspecified":
            return bool({"crustaceans", "molluscs"} & covered)
        if code in ("peanuts", "tree_nuts"):
            # Covered for now; the ambiguity flag makes reception ask which nuts.
            return "nuts_unspecified" in covered
        return False

    def _allergen_safety_net(self, note_text: str, covered: set[str]) -> list[Flag]:
        flags = []
        for code, words in allergens.find_allergens(note_text).items():
            if not self._is_covered(code, covered):
                flags.append(Flag(BLOCK, f"Safety net: the note mentions \"{', '.join(words)}\" "
                                         f"({allergens.label(code)}) but no allergy for it was extracted. "
                                         f"Check the note before confirming."))
        return flags

    @staticmethod
    def _carry_over_allergies(items: list[HandoffItem], covered: set[str]) -> list[Flag]:
        names = sorted(allergens.label(c) for c in covered)
        if not names:
            return []
        flags = []
        for i, item in enumerate(items):
            if item.request_type in (CELEBRATION, PICNIC):
                flags.append(Flag(WARNING, f"Guest allergy applies: {', '.join(names)}. "
                                           f"Food for this request must be suitable.", i))
        return flags

    @staticmethod
    def _escalate_complaints(items: list[HandoffItem]) -> list[Flag]:
        flags = []
        for i, item in enumerate(items):
            if item.request_type != COMPLAINT:
                continue
            text = (item.source_text + " " + str(item.details.get("issue", ""))).lower()
            if any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in REACTION_WORDS):
                flags.append(Flag(URGENT, "Possible allergic reaction. Tell the duty manager "
                                          "and head chef now.", i))
        return flags

    @staticmethod
    def _injection_warning(note_text: str) -> list[Flag]:
        lowered = note_text.lower()
        if any(p in lowered for p in INJECTION_PHRASES):
            return [Flag(WARNING, "The note contains instructions aimed at the AI. They were "
                                  "ignored; check the extracted requests carefully.")]
        return []