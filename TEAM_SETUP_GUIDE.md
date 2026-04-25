# Team Setup Guide

이 문서는 팀원이 로컬에서 프로젝트를 실행하기 위한 안내입니다.

## 1. 프로젝트 받기

```bash
git clone <repo-url>
cd SKN25-4th-5Team
```

## 2. 환경변수 파일 만들기

```bash
cp .env.example .env
```

`.env` 파일은 개인 로컬 설정 파일입니다. Git에 올리지 않습니다.

기본값 그대로 실행해도 됩니다. 필요하면 아래 값만 수정합니다.

```env
BACKEND_PORT=8000
FRONTEND_PORT=5173
POSTGRES_PASSWORD=change-this-db-password
```

`VITE_API_URL`은 비워둡니다.

```env
VITE_API_URL=
```

비워두면 React가 같은 도메인의 `/api/...`로 요청하고, frontend Nginx가 backend로 프록시합니다.

## 3. Docker 실행

```bash
docker compose up -d --build
```

## 4. DB 마이그레이션

```bash
docker compose exec backend python manage.py migrate
```

## 5. 접속 주소

```txt
Frontend: http://localhost:5173
API:      http://localhost:5173/api/hello/
Backend:  http://localhost:8000/api/hello/
```

일반적으로 프론트와 API는 아래 주소를 사용합니다.

```txt
http://localhost:5173
```

## 6. 상태 확인

```bash
docker compose ps
```

정상이라면 `backend`, `frontend`, `db` 서비스가 모두 실행 중이어야 합니다.

로그 확인:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

## 7. 종료

```bash
docker compose down
```

## 8. DB 비밀번호 변경 후 오류가 날 때

이미 PostgreSQL 볼륨이 만들어진 뒤 `.env`의 `POSTGRES_PASSWORD`를 바꾸면 DB 인증 오류가 날 수 있습니다.

기존 DB 데이터가 필요 없다면 아래처럼 볼륨까지 삭제 후 다시 실행합니다.

```bash
docker compose down -v
docker compose up -d --build
docker compose exec backend python manage.py migrate
```

주의: `down -v`는 DB 데이터를 삭제합니다.

## 9. 자주 쓰는 명령어

백엔드 쉘 접속:

```bash
docker compose exec backend bash
```

Django check:

```bash
docker compose exec backend python manage.py check
```

마이그레이션 생성:

```bash
docker compose exec backend python manage.py makemigrations
```

마이그레이션 적용:

```bash
docker compose exec backend python manage.py migrate
```

컨테이너 재빌드:

```bash
docker compose up -d --build
```

## 10. 현재 구조

```txt
Browser
  -> frontend Nginx :5173
      /       -> React build files
      /api/   -> backend:8000

backend
  -> Django + DRF + Gunicorn
  -> PostgreSQL db:5432

db
  -> PostgreSQL
```

## 11. 주의사항

- `.env`는 Git에 올리지 않습니다.
- `.env.example`만 팀원과 공유합니다.
- `VITE_API_URL`은 기본적으로 비워둡니다.
- API 호출은 프론트 기준 `/api/...` 경로를 사용합니다.
- DB 데이터를 삭제해도 되는 상황에서만 `docker compose down -v`를 사용합니다.
