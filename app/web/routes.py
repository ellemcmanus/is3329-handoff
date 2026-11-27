"""Flask routes. Each route reads the form, calls one component, and renders a page."""
from datetime import date

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from app import allergens
from app.intake import GuestNote
from app.review import ConfirmationError
from app.web import DEMO_STAFF

bp = Blueprint("web", __name__)


def services():
    return current_app.extensions["services"]


@bp.app_template_filter("allergen")
def allergen_label(code):
    return allergens.label(code)


@bp.route("/")
def home():
    return redirect(url_for("web.new_note"))


@bp.route("/note", methods=["GET", "POST"])
def new_note():
    s = services()
    if request.method == "POST":
        form = request.form
        try:
            note = GuestNote(guest_name=form["guest_name"].strip(), room=form["room"].strip(),
                             stay_start=date.fromisoformat(form["stay_start"]),
                             stay_end=date.fromisoformat(form["stay_end"]),
                             text=form["note_text"].strip())
        except (KeyError, ValueError):
            flash("Fill in the guest name, room, stay dates and note.")
            return render_template("note.html", form=form, examples=s.examples)
        if not (note.guest_name and note.room and note.text):
            flash("Fill in the guest name, room, stay dates and note.")
            return render_template("note.html", form=form, examples=s.examples)
        if note.stay_end < note.stay_start:
            flash("The stay end date is before the start date.")
            return render_template("note.html", form=form, examples=s.examples)

        note_id = s.intake.submit_note(note)
        return redirect(url_for("web.review", note_id=note_id))

    form = {}
    example = request.args.get("example", type=int)
    if example is not None and 0 <= example < len(s.examples):
        e = s.examples[example]
        form = {"guest_name": e["guest_name"], "room": e["room"], "stay_start": e["stay_start"],
                "stay_end": e["stay_end"], "note_text": e["note_text"]}
    return render_template("note.html", form=form, examples=s.examples)


@bp.route("/review/<int:note_id>")
def review(note_id):
    s = services()
    note = s.intake.get_note(note_id)
    if note is None:
        abort(404)
    return render_template("review.html", note=note, items=s.review.items_for_note(note_id),
                           staff=DEMO_STAFF)


@bp.route("/review/item/<int:item_id>/confirm", methods=["POST"])
def confirm(item_id):
    s = services()
    try:
        item = s.review.confirm(item_id, request.form.get("staff", ""),
                                safety_checked=request.form.get("safety_checked") == "yes")
        flash(f"Confirmed: {item.request_type}.")
    except ConfirmationError as e:
        flash(str(e))
        item = s.review.get_item(item_id)
        if item is None:
            abort(404)
    return redirect(url_for("web.review", note_id=item.note_id))


@bp.route("/briefing")
def briefing():
    s = services()
    default_day = s.settings.demo_today or date.today()
    try:
        day = date.fromisoformat(request.args.get("date", default_day.isoformat()))
    except ValueError:
        day = default_day
    service = request.args.get("service", "dinner")
    if service not in ("lunch", "dinner"):
        service = "dinner"
    return render_template("briefing.html", briefing=s.briefing.build(day, service))