"""Web layer (Reception UI and Kitchen view) and the app's composition root.

create_app() builds every component once and connects them through their
interfaces. The routes only call those interfaces; no business logic here.
"""
import json

from flask import Flask

from app import db
from app.bookings import CsvBookingProvider
from app.briefing import BriefingService
from app.config import Settings, create_extractor, load_settings
from app.guests import GuestRepository
from app.handlers import create_handlers
from app.intake import IntakeService
from app.review import ReviewService
from app.safety import SafetyChecker

# Identity and access is Mocked in the prototype: a fixed list of demo staff.
DEMO_STAFF = ["Aoife (reception)", "Conor (reception)", "Niamh (duty manager)"]


class Services:
    def __init__(self, settings: Settings):
        conn = db.connect(settings.database)
        self.settings = settings
        self.guests = GuestRepository(conn)
        self.bookings = CsvBookingProvider(settings.bookings_file)
        self.review = ReviewService(conn, self.guests)
        self.intake = IntakeService(conn, create_extractor(settings), create_handlers(settings.demo_today),
                                    SafetyChecker(), self.guests, self.bookings, self.review)
        self.briefing = BriefingService(self.bookings, self.guests, self.review)
        with open(settings.notes_file, encoding="utf-8") as f:
            self.examples = json.load(f)  # synthetic notes offered on the New note page


def create_app(settings: Settings | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = "demo-only-not-secret"  # only used for flash messages in the demo
    app.extensions["services"] = Services(settings or load_settings())

    from app.web.routes import bp
    app.register_blueprint(bp)
    return app