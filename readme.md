# URL Shortener Service
 
A production-ready REST API for shortening URLs, built with FastAPI and SQLAlchemy.
 
---
 
## Architecture
 
```
Client → FastAPI Routes → Service Layer → Repository Layer → SQLite/PostgreSQL
                                ↓
                         In-Memory Cache (TTL: 5min)
```
 
### Request Cycle and Data Flow
 
```
POST /shorten
    → Pydantic validates input
    → Custom alias OR generate random short code (7 chars)
    → Check collision in DB (unique constraint)
    → Save to DB
    → Cache short_code → long_url (TTL 5 min)
    → Return UrlResponse
 
GET /{short_code}
    → Check in-memory cache
        → Cache HIT  → increment access count → 307 Redirect
        → Cache MISS → query DB → populate cache → 307 Redirect
        → Not found  → 404
 
GET /meta/{short_code}
    → Query DB directly
    → Return created_at, access_count, short_url
 
GET /health
    → Returns service status
```
 
### Layer Responsibilities
 
| Layer | Responsibility |
|---|---|
| Routes (main.py) | Receive requests, call service, return responses |
| Service | Business logic — collision handling, caching, code generation |
| Repository | Data access abstraction — swappable storage backend |
| Cache | In-memory TTL cache — reduces DB load |
| Entity | Pydantic models for validation, SQLAlchemy models for DB |
 
---
 
## Tech Stack
 
- **FastAPI** — REST framework with auto Swagger docs
- **SQLAlchemy** — ORM, works with SQLite locally and PostgreSQL on DigitalOcean
- **Pydantic** — Automatic input validation and serialization
- **In-Memory Cache** — TTL-based caching layer (Redis-ready)
- **pytest** — Unit and integration testing
---
 
## Project Structure
 
```
URLShortner/
├── main.py                   # FastAPI app and routes
├── database.py               # DB connection and session management
├── readme.md                 # This file
├── Entity/
│   └── urlentity.py          # Pydantic + SQLAlchemy models
├── Repository/
│   └── url_repository.py     # Data access layer
├── Service/
│   └── url_service.py        # Business logic
├── Cache/
│   └── cache.py              # In-memory TTL cache
└── tests/
    └── test_api.py           # Unit and integration tests
```
 
---
 
## Setup and Running Locally
 
### Install Dependencies
 
```bash
pip install fastapi uvicorn sqlalchemy pytest httpx
```
 
### Run Locally
 
```bash
uvicorn main:app --reload
```
 
### View API Docs
 
```
http://localhost:8000/docs
```
 
---
 
## Environment Variables
 
| Variable | Default | Description |
|---|---|---|
| DATABASE_URL | sqlite:///./urls.db | Database connection string |
 
### Switch to PostgreSQL (Zero Code Changes)
 
```bash
export DATABASE_URL=postgresql://user:password@host:5432/dbname
```
 
---
 
## API Endpoints
 
| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| GET | /health | Health check | 200 |
| POST | /shorten | Create short URL | 201 |
| GET | /{short_code} | Redirect to long URL | 307 |
| GET | /meta/{short_code} | Get URL metadata | 200 |
 
### POST /shorten — Request Body
 
```json
{
  "long_url": "https://www.google.com",
  "custom_alias": "google"
}
```
 
### POST /shorten — Response
 
```json
{
  "short_code": "zsNcwvD",
  "long_url": "https://www.google.com",
  "short_url": "https://short.ly/zsNcwvD",
  "created_at": "2026-06-08T05:47:47.446258",
  "access_count": 0
}
```
 
---
 
## Running Tests
 
```bash
PYTHONPATH=. pytest tests/ -v
```
 
---
 
## Error Handling
 
| Scenario | HTTP Code | Response |
|---|---|---|
| Invalid input | 422 | Validation error detail |
| Custom alias taken | 409 | Alias already taken |
| Short code not found | 404 | URL not found |
| Code generation failed | 500 | Could not generate unique code |
 
---
 
## Thread Safety and Concurrency
 
- DB unique constraint on short_code handles race conditions atomically
- Concurrent requests attempting same alias — only one succeeds, others get 409
- Cache layer is single-instance safe with TTL expiry
- In production: PostgreSQL handles concurrent writes reliably at scale
---
 
## Trade-offs and Future Improvements
 
| What | Current | Production |
|---|---|---|
| Storage | SQLite | PostgreSQL |
| Cache | In-memory | Redis distributed cache |
| Authentication | None | API Key or JWT Bearer |
| Rate limiting | None | Token bucket per API key |
| Short code generation | Random 7 chars | Base62 encoded incremental ID |
| Analytics | Access count only | Full click analytics with timestamps |
| Deployment | Single instance | Horizontal scaling behind load balancer |
 
---
 
## Deployment on DigitalOcean
 
### App Platform
 
1. Push code to GitHub
2. Connect repo to DigitalOcean App Platform
3. Set DATABASE_URL environment variable to PostgreSQL connection string
4. App auto-deploys on every push to main branch
### Run Command
 
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```
 
### Managed PostgreSQL
 
1. Create Managed Database on DigitalOcean
2. Copy the connection string from the dashboard
3. Set it as the DATABASE_URL environment variable
4. Zero code changes required — SQLAlchemy handles the rest
---
 
## CI/CD
 
This project uses GitHub Actions for automated testing and deployment.
 
On every push to main:
1. Run pytest test suite
2. On passing tests, auto-deploy to DigitalOcean App Platform