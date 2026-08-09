# Zhenya Automation

Telegram workflow for extracting rental requirements, parsing property offers
from supported sites and calculating match scores.

## Structure

- `clients/` — external AI and HTTP clients.
- `config/` — application constants.
- `parsers/` — HTML parsers and URL-to-parser routing.
- `schemas/` — Pydantic models and the client-requirements JSON Schema.
- `services/` — application use cases: requirements, offers and matching.
- `tg_bot/` — Telegram handlers, keyboards, file downloads and startup wiring.
- `tests/` — unit tests without external network calls.
- `scripts/` — manual diagnostic commands.

Dependencies point inward: `tg_bot → services → parsers/clients/schemas`.
Services do not import Telegram classes.

## Run

From the project root:

```bash
.venv/bin/python main.py
```

Alternatively:

```bash
.venv/bin/python -m tg_bot
```

The old `.venv/bin/python tg_bot/bot.py` command remains supported for existing
IDE run configurations.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

To add another property site, implement a parser based on `BaseParser` and
register its domain in `parsers/router.py`.
