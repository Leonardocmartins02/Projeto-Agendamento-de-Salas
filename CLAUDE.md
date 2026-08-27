# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Setup (Windows PowerShell):
```
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Setup (Linux/macOS):
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

Run the dev server:
```
python app.py
```
Serves at `http://127.0.0.1:5000` with `debug=True`. On first run it creates `agendamentos.db` (SQLite) and seeds 3 example rooms if the `Sala` table is empty. The DB URI can be overridden with the `DATABASE_URL` env var.

Run tests:
```
pytest
```
Run a single test: `pytest tests/test_agendamentos.py::TestCriacao::test_bloqueia_conflito_de_horario`

There is no linter or build step in this repo currently.

Reset the database: stop the server, delete `agendamentos.db`, restart (schema + seed rooms are recreated automatically).

## Architecture

Flask backend (`app.py`) serving a server-rendered template plus a vanilla JS/CSS frontend — no build tooling, no frontend framework.

- **`app.py`**: app-factory pattern (`create_app(config=None)`) plus SQLAlchemy models and all REST routes.
  - Models: `Sala` (id, nome, capacidade) and `Agendamento` (id, sala_id FK, responsavel, data_inicio, data_fim). Both expose `to_json()`.
  - Routes: `GET /salas`, `GET /salas/<id>/agendamentos`, `GET /agendamentos`, `POST /agendamentos`, `PUT /agendamentos/<id>`, `DELETE /agendamentos/<id>`, plus `GET /` rendering `templates/index.html`.
  - `POST` and `PUT` both validate the full payload (`_validar_payload_agendamento`, `_parse_sala_id`, `_parse_datas`) before touching the DB — missing/invalid fields return 400, not a 500 crash. Both also run the same overlap check: conflict when `data_inicio_nova < data_fim_existente` and `data_fim_nova > data_inicio_existente` for the same `sala_id` (409); `PUT` excludes the record being edited from that check.
  - **Concurrency**: SQLite normally opens transactions "deferred", so two concurrent requests can both pass the conflict SELECT before either commits (double-booking). This repo forces `BEGIN IMMEDIATE` on every SQLite transaction via SQLAlchemy `connect`/`begin` engine events — the second concurrent writer blocks until the first commits, then re-runs its own conflict check and correctly sees the just-committed row. This is a SQLite-specific stopgap; a real multi-instance deployment should move to Postgres with row locking (`SELECT ... FOR UPDATE`) instead.
  - Dates are ISO strings (`YYYY-MM-DDTHH:mm` from `datetime-local` inputs), parsed with `datetime.fromisoformat`. Stored as naive datetimes (no timezone) — fine for single-timezone deployments only.
- **`templates/index.html`**: single page, two-column layout — room list on the left, agendamentos + form for the selected room on the right.
- **`static/js/script.js`**: talks to the API via relative `fetch` calls (`API_URL = ''`) since the Flask app serves its own frontend. Handles room selection, create/edit/delete of agendamentos, accent-insensitive room search (`normalizeText`, NFD-based) with debounce, and toast/`aria-live` feedback.
- **`static/css/style.css`**: CSS custom-property tokens, dark mode via `prefers-color-scheme`.
- **`tests/`**: functional tests hitting the real Flask routes via `test_client()`, each test getting a fresh temp-file SQLite DB (`tests/conftest.py`). Includes a threaded test (`TestConcorrencia`) that fires two simultaneous conflicting `POST /agendamentos` and asserts exactly one succeeds — this is the regression test for the concurrency fix above.

## Notes

- No auth/authorization yet — anyone can create/edit/delete any agendamento. Planned for a later pass (JWT).
- `venv/` must never be committed — it's gitignored; if `git status` ever shows `venv/*` as new/modified, something's wrong with the local checkout, not the ignore rule.
