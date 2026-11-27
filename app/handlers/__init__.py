"""Registry of request handlers, one per request type."""
from datetime import date

from app.handlers.allergy import AllergyHandler
from app.handlers.base import RequestHandler
from app.handlers.celebration import CelebrationHandler
from app.handlers.complaint import ComplaintHandler
from app.handlers.picnic import PicnicHandler
from app.models import ALLERGY, CELEBRATION, COMPLAINT, PICNIC


def create_handlers(today: date | None = None) -> dict[str, RequestHandler]:
    return {
        ALLERGY: AllergyHandler(today),
        CELEBRATION: CelebrationHandler(today),
        COMPLAINT: ComplaintHandler(today),
        PICNIC: PicnicHandler(today),
    }