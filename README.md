# Pyroswiki

A Python reimplementation of the [Foswiki](https://foswiki.org/) enterprise wiki platform, built with a FastAPI backend and a Jinja2 web UI.

---

## Overview

Pyroswiki provides a modern, async Python wiki engine that is broadly compatible with Foswiki's Topic Markup Language (TML) and URL conventions. It is structured as two cooperating services:

| Service | Description | Default port |
|---------|-------------|--------------|
| **API** | FastAPI REST backend | 8621 (internal) / 8443 (nginx) |
| **Web UI** | Jinja2 server-rendered frontend | 8221 (internal) / 443 (nginx) |

The API is the source of truth. The Web UI is a thin client that renders pages server-side and proxies uploads/downloads through the API.

---

## Features

- **Webs and Topics** — Foswiki-compatible hierarchical wiki structure
- **TML rendering** — headings (`---++`), bold (`*text*`), italic (`_text_`), bracket links (`[[Target][Label]]`), WikiWord auto-linking
- **Macro expansion** — `%WIKIUSERNAME%`, `%PUBURL%`, `%ATTACHURL%`, `%INCLUDE%`, `%SEARCH%`, `%TOC%`, `%IF%`, `%DATE%`, `%USERINFO%`, and more
- **Attachments** — file upload/download with Foswiki-compatible `/pub/{web}/{topic}/{file}` URLs
- **DataForms** — structured form schemas attached to topics
- **ACL** — per-topic and per-web access control (view/change/rename/delete)
- **User management** — registration, JWT auth, password reset via email, admin controls
- **Groups** — wiki group membership for ACL evaluation
- **Plugins** — hook-based plugin system with pre/post render hooks
- **RSS/Atom feeds** — global and per-web change feeds
- **Admin API** — site config, user management, statistics
- **Render cache** — rendered HTML cached per topic version in the database; user-specific macros bypass the cache
- **Full test suite** — 125+ tests across 7 test modules

---

## Project Structure

```
py-foswiki/
├── app/                    # FastAPI backend
│   ├── core/               # Config, database, security
│   ├── models/             # SQLAlchemy ORM models
│   ├── routes/             # API route handlers
│   │   ├── auth.py         # JWT authentication
│   │   ├── webs.py         # Web (namespace) management
│   │   ├── topics.py       # Topic CRUD + rendering
│   │   ├── attachments.py  # File attachments
│   │   ├── search.py       # Full-text search
│   │   ├── forms.py        # DataForms
│   │   ├── feeds.py        # RSS/Atom feeds
│   │   └── admin.py        # Admin API
│   └── services/
│       ├── renderer.py     # TML/Markdown render pipeline
│       ├── macros/         # Macro engine + built-in macros
│       ├── wikiword/       # WikiWord auto-linker
│       ├── acl.py          # Access control
│       ├── plugins.py      # Plugin manager
│       └── ...
├── webui/                  # Jinja2 web UI (separate FastAPI app)
│   ├── pages/              # Route handlers (topics, webs, users, etc.)
│   └── templates/          # HTML templates
├── tests/                  # pytest test suite
├── alembic/                # Database migrations
├── deploy/                 # Systemd units, nginx config, deployment guide
├── scripts/                # Migration and utility scripts
├── docker/                 # Docker Compose setup
└── .env.example            # Environment configuration template
```

---

## Quick Start (Development)

**Prerequisites:** Python 3.11+, PostgreSQL

```bash
# Clone and set up
git clone https://github.com/peterlharding/pyroswiki.git
cd pyroswiki
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: set DATABASE_URL, SECRET_KEY

# Run migrations
PYTHONPATH=. alembic upgrade head

# Start API (port 8621)
make api
# or: uvicorn app.main:app --host 0.0.0.0 --port 8621 --reload

# Start Web UI (port 8221) in another terminal
make web
# or: uvicorn webui.app:app --host 0.0.0.0 --port 8221 --reload
```

Then open http://localhost:8221 for the web UI or http://localhost:8621/api/docs for the interactive API docs.

---

## Configuration

All settings are read from a `.env` file (or environment variables). Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `BASE_URL` | Public API URL | `http://localhost:8621` |
| `WEB_BASE_URL` | Public web UI URL (for attachment links) | *(same as BASE_URL)* |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key — **change in production** | — |
| `ATTACHMENT_ROOT` | Filesystem path for uploaded files | `./data/attachments` |
| `ALLOW_REGISTRATION` | Allow public self-registration | `true` |
| `SMTP_HOST` | SMTP server for password reset emails | *(disabled)* |

See `.env.example` for the full list.

---

## Running Tests

```bash
# All tests (uses SQLite in-memory)
pytest

# Specific module
pytest tests/test_02_macros.py -v
```

Tests use an in-memory SQLite database and do not require a running PostgreSQL instance.

---

## Production Deployment

See [`deploy/README.md`](deploy/README.md) for full instructions covering:
- Systemd service units (`pyroswiki-api`, `pyroswiki-web`)
- nginx reverse proxy configuration with SSL
- Database setup and migration
- First admin user bootstrap

### Deploying updates

```bash
# On the server
cd /opt/pyroswiki
git pull
systemctl restart pyroswiki-api pyroswiki-web

# If database schema changed
PYTHONPATH=. .venv/bin/alembic upgrade head
```

---

## Foswiki Compatibility

Pyroswiki is designed to import content from an existing Foswiki instance. The `scripts/` directory contains migration utilities:

| Script | Purpose |
|--------|---------|
| `scripts/migrate_cfp.py` | Migrate topics from a source Foswiki via its REST API |
| `scripts/migrate_attachments.py` | Download and re-upload referenced attachments |

Attachment URLs use the Foswiki-compatible `/pub/{web}/{topic}/{filename}` path, served directly by the web UI.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ASGI server | [Uvicorn](https://www.uvicorn.org/) |
| Database ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) |
| Database | PostgreSQL (production) / SQLite (tests) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Templating | [Jinja2](https://jinja.palletsprojects.com/) |
| Markup rendering | [mistune](https://mistune.lepture.com/) |
| Auth | JWT (python-jose) + bcrypt |
| Settings | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Email | aiosmtplib |

---

## License

MIT — see [LICENSE](LICENSE).
