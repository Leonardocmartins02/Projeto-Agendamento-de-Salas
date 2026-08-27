# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Setup (Windows PowerShell):
```
python -m venv venv
venv\Scripts\Activate.ps1
pip install Flask==2.* Flask-SQLAlchemy==3.* Flask-Cors==4.*
```

Setup (Linux/macOS):
```
python3 -m venv venv
source venv/bin/activate
pip install Flask==2.* Flask-SQLAlchemy==3.* Flask-Cors==4.*
```

Run the dev server:
```
python app.py
```
Serves at `http://127.0.0.1:5000` with `debug=True`. On first run it creates `agendamentos.db` (SQLite) and seeds 3 example rooms if the `Sala` table is empty.

There is no test suite, linter, or build step in this repo currently.

Reset the database: stop the server, delete `agendamentos.db`, restart (schema + seed rooms are recreated automatically).

## Architecture

Single-file Flask backend (`app.py`) serving a server-rendered template plus a vanilla JS/CSS frontend — no build tooling, no frontend framework.

- **`app.py`**: Flask app, SQLAlchemy models, and all REST routes in one file.
  - Models: `Sala` (id, nome, capacidade) and `Agendamento` (id, sala_id FK, responsavel, data_inicio, data_fim). Both expose `to_json()`.
  - Routes: `GET /salas`, `GET /salas/<id>/agendamentos`, `GET /agendamentos`, `POST /agendamentos`, `PUT /agendamentos/<id>`, `DELETE /agendamentos/<id>`, plus `GET /` rendering `templates/index.html`.
  - Overlap validation lives in `POST /agendamentos`: a conflict exists when `data_inicio_nova < data_fim_existente` and `data_fim_nova > data_inicio_existente` for the same `sala_id` — returns 409. `data_fim <= data_inicio` returns 400. Note `PUT /agendamentos/<id>` does **not** re-run this conflict check, unlike POST.
  - Dates are ISO strings (`YYYY-MM-DDTHH:mm` from `datetime-local` inputs), parsed with `datetime.fromisoformat`.
- **`templates/index.html`**: single page, two-column layout — room list on the left, agendamentos + form for the selected room on the right.
- **`static/js/script.js`**: talks to the API via `fetch` against `API_URL = 'http://127.0.0.1:5000'` (hardcoded, not relative — matters if the app is ever served from a different origin/port). Handles room selection, create/edit/delete of agendamentos, accent-insensitive room search (`normalizeText`, NFD-based) with debounce, and toast/`aria-live` feedback.
- **`static/css/style.css`**: CSS custom-property tokens, dark mode via `prefers-color-scheme`.

## Notes

- `.gitignore` currently has stray shell-prompt text mixed into it (leftover from a copy-paste) rather than clean ignore patterns — worth cleaning up before it causes a bad ignore rule.
- No `venv/` should be committed; the repo currently has a `venv/` directory checked out locally (from clone) — confirm it's actually gitignored, not tracked.
