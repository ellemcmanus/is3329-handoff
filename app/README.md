# Reception-to-kitchen hand-off tool 


# Reception-to-kitchen hand-off tool (IS3329 prototype, Deliverable 2)

**Repository:** https://github.com/ellemcmanus/is3329-handoff  


Reception pastes a guest's note (allergies, celebrations, picnic orders, food complaints)...
Reception pastes a guest's note (allergies, celebrations, picnic orders, food complaints).
The app splits it into separate requests, checks them with safety rules, lets reception
confirm each one, and produces a kitchen briefing ordered by seating time.

**I have only used synthetic data (made-up).** No real guest, staff or booking data is in this project.

## Requirements

- Python 3.10 or newer
- No API key is needed: the AI component runs as a mock in this deliverable.

## Install

```bash
cd handoff
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

Then copy the settings file:

```bash
# Windows:      copy .env.example .env
# macOS/Linux:  cp .env.example .env
```

## Run the app

```bash
python run.py
```

Open http://127.0.0.1:5000 in a browser.

**Demo walkthrough**

1. On **New note**, click a synthetic example (start with *Murphy, room 3*), then **Analyse note**.
2. On the review screen, compare each request with the original note, pick a staff name and **Confirm request**.
3. Try *Byrne, room 4*: the mock AI misses "no walnuts", and the safety net blocks confirmation until
   "I have checked the note" is ticked.
4. Open **Kitchen briefing** and choose **Friday 4 December 2026, dinner** to see the confirmed requests
   ordered by seating time. Thursday 3 December shows the Murphy picnic.
5. *Fitzgerald, room 15* simulates an AI failure: the app does not crash and the safety net still runs.

The database file (`handoff.db`) is created on first run. Delete it to start again.

## Run the tests

pytest
Expected result: **43 passed**.

```bash
pytest
```

All tests use the mock AI and a fresh in-memory database, so they are fast and repeatable.

## How the code maps to the architecture

| Component (D1 diagram) | Folder | Interface                                             | Prototype label |
| --- | --- |-------------------------------------------------------| --- |
| Note sources / Reception UI | `app/web/` | Flask routes and templates                            | Simplified |
| Intake gateway | `app/intake/` | `IntakeService.submit_note(note)`                     | Simplified (direct calls replace the event bus) |
| Request extractor (AI) | `app/extractor/` | `RequestExtractor.extract(note_text)`                 | Mock now; `LLMExtractor` stub for D3 |
| Request handlers | `app/handlers/` | `RequestHandler.validate(request, guest)`             | Built |
| Safety rules engine | `app/safety/` | `SafetyChecker.check(note_text, items, guest)`        | Built |
| Guest profile store | `app/guests/` | `GuestRepository.get / find / save`                   | Simplified (SQLite) |
| Booking provider | `app/bookings/` | `BookingProvider.get_bookings(guest, day)`            | Mocked (CSV file) |
| Review and confirmation | `app/review/` | `ReviewService.confirm(item_id, staff, safety_checked)` | Built |
| Briefing service | `app/briefing/` | `BriefingService.build(day, service)`                 | Built |
| Kitchen view | `app/web/templates/briefing.html` | printable page                                        | Simplified |
| Identity and access | `app/web/__init__.py` (`DEMO_STAFF`) | fixed staff list                                      | Mocked |
| Event bus, notifications, data retention | none | none                                                  | Simplified / Deferred |

Shared data shapes are in `app/models.py`. The 14 EU allergens and their keywords are in `app/allergens.py`.
`app/web/__init__.py` is the only place where components are created and connected.

## Switching the AI from mock to real

Set `EXTRACTOR=llm` in `.env`. Only `app/config.py` reads this setting, so nothing else changes.
`LLMExtractor` is planned for Deliverable 3 and currently reports itself as unavailable, which also
shows the app's fallback when the AI fails.

## Known limitations (planned for D3)

- The real LLM extractor is not implemented yet.
- Requests cannot be edited on the review screen; the manual-entry form for AI failures is not built yet.
- When a blocked request is confirmed after checking the note, the missed allergen is not yet added automatically.
- The keyword safety net only knows the words in `app/allergens.py`, misspellings (e.g. "mussles") are not caught.

## Use of generative AI

Generative AI (Claude, Anthropic) was used in developing this project, Full details are in section 8 of the
technical document.
