# Bible Art App

Initial project structure for a Bible-themed art application.

## Project Structure

- `backend/` Flask backend and SQLite integration
- `frontend/` placeholder for the front-end app
- `api/` placeholder for API docs/specs
- `data/` SQLite database storage (`bible_art.db`)

## Backend Files

- `backend/app.py` Flask application with starter API routes
- `backend/database.py` SQLite connection and initialization helpers
- `backend/models.py` entity dataclasses and SQL schema
- `backend/seed_data.py` seeds sample Old and New Testament data

## Entities

- Testaments
- Stories
- Characters
- Locations
- Artworks
- Artists

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Initialize and Seed Database

```bash
python backend/seed_data.py
```

## Run the Flask App

```bash
python backend/app.py
```

API endpoints:

- `GET /health`
- `GET /api/testaments`
- `GET /api/stories`
- `GET /api/artworks`
