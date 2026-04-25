# SKN25-4th-5Team

Django + React + PostgreSQL Docker project.

## Stack

- Backend: Django, Django REST framework, Gunicorn
- Frontend: React, Vite, Nginx
- Database: PostgreSQL
- Infra: Docker Compose

## Quick Start

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend python manage.py migrate
```

## URLs

- Frontend: http://localhost:5173
- API through frontend Nginx: http://localhost:5173/api/hello/
- Backend direct: http://localhost:8000/api/hello/

## Common Commands

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose down
```

## Environment

Do not commit `.env`. Use `.env.example` as the shared template.

For local development, `VITE_API_URL` can stay empty so the React app calls `/api/...` through Nginx.
