# Job Application Tracker

A full-stack application for organizing job applications, tracking interview progress, and managing the job search in one place.

Built with React, FastAPI, and PostgreSQL.

## Live Demo

[Open the application]( https://job-application-tracker-4kus.onrender.com )

Create an account to explore the application. Each account has its own private application list.

## Features

- User registration and login
- JWT authentication and Argon2 password hashing
- User-specific access to applications
- Create, view, edit, and delete job applications
- Track statuses: Applied, Interview, Offer, and Rejected
- Search by company or position
- Filter applications by status
- Paginated application list
- Dashboard summary with totals by status
- Responsive English-language interface

## Screenshots

### Sign In
![Sign-in page](docs/screenshots/sign-in.png)

### Dashboard
![Application dashboard](docs/screenshots/dashboard.png)

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, JavaScript, Vite, CSS |
| Backend | Python, FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy, psycopg |
| Migrations | Alembic |
| Authentication | PyJWT, pwdlib, Argon2 |
| Hosting | Render |
| Database hosting | Neon |

## Architecture

The React frontend communicates with the FastAPI backend through HTTP requests.

Backend responsibilities are separated into:

- **Routers:** request handling, dependencies, and HTTP responses
- **Schemas:** input validation and response serialization
- **Services:** application logic and database operations
- **Models:** SQLAlchemy table definitions and relationships

Application queries are scoped to the authenticated user. Requests for another user's application return `404`.

## Project Structure

```text
job-application-tracker/
├── alembic/
│   └── versions/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── models/
├── routers/
├── schemas/
├── services/
├── docs/
│   └── screenshots/
├── database.py
├── security.py
├── main.py
├── alembic.ini
└── requirements.txt
```

## Run Locally

Prerequisites:

- Python compatible with the pinned dependencies
- Node.js compatible with the Vite version in `frontend/package-lock.json`
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/faridhajiyev03/job-application-tracker.git
cd job-application-tracker
```

### 2. Install backend dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.

### 3. Configure environment variables

Create a PostgreSQL database and a role with permission to create tables.

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/job_application_tracker
JWT_SECRET_KEY=REPLACE_WITH_A_RANDOM_SECRET
```

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Never commit `.env` or real credentials.

### 4. Apply migrations

```bash
python -m alembic upgrade head
```

Use migrations to initialize a new database and apply schema changes.

### 5. Start the backend

```bash
python -m uvicorn main:app --reload --port 8000
```

API documentation: http://127.0.0.1:8000/docs

### 6. Start the frontend

In a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173.

During development, Vite forwards `/api` requests to FastAPI on port `8000`.

## Production Build

From the project root:

```bash
npm --prefix frontend ci
npm --prefix frontend run build
```

Restart FastAPI after building. It serves the generated frontend from `frontend/dist` at `/`.

### Render configuration

**Build command**

```bash
pip install -r requirements.txt && npm --prefix frontend ci && npm --prefix frontend run build
```

**Start command**

```bash
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set `DATABASE_URL` and `JWT_SECRET_KEY` in the Render environment settings. Use a Node.js version compatible with the project's Vite version.

Health check endpoint: `/health`

## API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Get an access token |
| GET | `/auth/me` | Get the authenticated user |
| POST | `/applications/` | Create an application |
| GET | `/applications/` | List, search, and filter own applications |
| GET | `/applications/summary` | Get own application statistics |
| GET | `/applications/{id}` | Get one application |
| PATCH | `/applications/{id}` | Update an application |
| DELETE | `/applications/{id}` | Delete an application |

The same endpoints are available under `/api` for the frontend.

Protected endpoints require:

```text
Authorization: Bearer <access_token>
```

## Security and Scope

- Passwords are stored as Argon2 hashes.
- Access tokens expire after 30 minutes.
- Application ownership is enforced on the backend.
- The frontend stores the access token in session storage.
- Secrets are supplied through environment variables.

This is a portfolio project. Email verification, password recovery, and refresh tokens are not implemented.

## Author

[Farid Hajiyev](https://github.com/faridhajiyev03)