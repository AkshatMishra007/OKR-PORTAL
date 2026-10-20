# OKR Backend API

A robust, enterprise-grade RESTful API backend for managing **Objectives and Key Results (OKRs)**, Organizations, Batches, Weekly Updates, Metric Trackers, FOGS & Hurdles, and Role-Based Access Control (RBAC).

Built with **Python 3.13**, **FastAPI**, **SQLAlchemy 2.0**, and **PostgreSQL**.

---

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Async Web Framework)
- **Database ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Database Engine**: [PostgreSQL](https://www.postgresql.org/) (via `psycopg2-binary`)
- **Data Validation & Schemas**: [Pydantic v2](https://docs.pydantic.dev/)
- **Authentication & Security**: JWT (JSON Web Tokens) via `python-jose` & `passlib` with `bcrypt`
- **Testing**: [pytest](https://docs.pytest.org/) with `httpx` / FastAPI `TestClient`
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)

---

## Key Features & Modules

- **Authentication & Authorization (`app/auth`, `app/rbac`)**: User registration, login, JWT token issuance/refresh, and fine-grained Role-Based Access Control (RBAC).
- **Organization Management (`app/organizations`, `app/organization_members`)**: Multi-tenant organization support, member invitations, user mapping, and logo upload handling.
- **Batch Management (`app/batches`, `app/batch_members`)**: Quarterly OKR cycles (JFM, AMJ, JAS, OND), batch scheduling, status management, and member assignments.
- **OKR Management (`app/my_okr`)**: Creation and tracking of Objectives, Key Results, targets, assignment, and tracker toggles.
- **Weekly Progress Updates (`app/weekly_update`)**: Weekly percentage progress logging and status remarks.
- **Metric Tracker Entries (`app/tracker_entries`)**: Numerical metric tracking with automatic progress calculation and target string parsing.
- **FOGS & Hurdles (`app/fogs_hurdles`)**: Logging and tracking challenges, obstacles (fogs & hurdles), and resolution action points.
- **Queries & Activities (`app/queries`, `app/query_activity`)**: Q&A, comments, and activity logging for OKRs.

---

## Setup & Local Development Guide

### Prerequisites

- **Python 3.11+** (Python 3.13 recommended)
- **PostgreSQL 14+** (running locally or via Docker)

---

### Step 1: Clone the Repository & Navigate

```bash
git clone <repository-url>
cd OKR-Backend
```

---

### Step 2: Set Up Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies

```bash
pip install -r app/requirements.txt
```

---

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory:

```env
DATABASE_URL=postgresql+psycopg2://postgres:1234@localhost:5432/okr
SECRET_KEY=okr-development-secret-key-change-later
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Ensure your PostgreSQL database named `okr` exists on your system.

---

### Step 5: Database Migrations

Run database schema migrations using Alembic:

```bash
alembic upgrade head
```

---

### Step 6: Start the Development Server

Run Uvicorn with auto-reload:

```bash
uvicorn app.main:app --reload
```

The server will start at: **`http://127.0.0.1:8000/api`**

---

### Step 7: Explore API Documentation

FastAPI provides interactive Swagger documentation automatically:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### Running Automated Tests

Run the test suite using `pytest`:

```bash
# Run all tests
.\venv\Scripts\pytest

# Run tests for a specific module (e.g. FOGS & Hurdles)
.\venv\Scripts\pytest app/tests/fogs_hurdles/
```

---

## Project Structure

```text
OKR-Backend/
├── alembic/              # Database migration scripts
├── app/                  # Application source code
│   ├── auth/             # Authentication & JWT routes
│   ├── batches/          # OKR Batches management
│   ├── batch_members/    # Batch member mappings
│   ├── common/           # Shared models, exceptions & handlers
│   ├── core/             # Database session & config settings
│   ├── fogs_hurdles/     # FOGS & Hurdles module
│   ├── my_okr/           # Core OKR management module
│   ├── organization_members/ # Organization member management
│   ├── organizations/    # Organization creation & logo management
│   ├── queries/          # OKR queries & Q&A module
│   ├── query_activity/   # Query activity logging
│   ├── rbac/             # Roles & permissions management
│   ├── tracker_entries/  # Weekly metric tracking
│   ├── users/            # User account management
│   ├── weekly_update/    # Weekly progress updates
│   ├── main.py           # FastAPI application entrypoint
│   └── tests/            # Automated test suite
├── docs/                 # Project documentation & status reports
├── .env                  # Environment variables
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Project requirements
└── README.md             # Repository documentation
```