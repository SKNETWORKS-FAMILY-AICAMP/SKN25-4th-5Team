# SKN25-4th-5Team — AI 기반 국내 여행 추천 시스템

> RAG(검색 증강 생성)와 벡터 유사도 검색을 활용한 맞춤형 여행지 추천 및 일정 생성 서비스

---

## 프로젝트 개요

사용자의 여행 조건(지역, 목적, 동행자, 이동 수단 등)과 행동 패턴을 분석해 국내 여행지를 추천하고, AI 챗봇을 통해 개인화된 다일 여행 일정을 자동 생성합니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **여행지 추천** | 지역·카테고리·동행자 유형 기반 맞춤 추천 |
| **일정 생성** | 출발지, 여행 유형, 기간(1~14일) 입력 시 시간대별 코스 자동 생성 |
| **AI 챗봇** | 여행 관련 질문에 대한 대화형 AI 응답 (대화 히스토리 유지) |
| **벡터 검색** | pgvector를 이용한 의미 기반 장소 검색 |

---

## 기술 스택

### Frontend
- **React 19** + **Vite**
- React Router DOM 7
- CSS Modules
- Nginx (프로덕션 서빙)

### Backend
- **Django 6** + **Django REST Framework**
- Python 3.12 / Gunicorn
- django-cors-headers

### AI / ML
- **OpenAI GPT-4o-mini** — 대화 생성 및 일정 작성
- **OpenAI text-embedding-3-small** — 1536차원 임베딩
- **LangChain** — RAG 파이프라인 오케스트레이션

### Database
- **PostgreSQL 16** + **pgvector** 확장
  - `travel_place_vectors` — 여행지 임베딩 테이블
  - `user_behavior_vectors` — 사용자 행동 패턴 임베딩 테이블

### 인프라
- **Docker** / **Docker Compose** — 멀티 컨테이너 구성

---

## 디렉토리 구조

```
SKN25-4th-5Team/
├── frontend/                   # React + Vite 앱
│   ├── src/
│   │   ├── pages/              # Home, Chatbot, Search, Schedule 페이지
│   │   ├── components/         # 재사용 UI 컴포넌트
│   │   ├── routes/             # React Router 설정
│   │   ├── utils/              # 유틸 함수
│   │   └── styles/             # CSS 모듈
│   ├── Dockerfile
│   └── nginx.conf
│
├── backend/                    # Django REST API
│   ├── config/                 # Django 설정 (settings, urls, wsgi, asgi)
│   ├── apps/
│   │   ├── chat/               # 채팅 API (세션·메시지 CRUD)
│   │   ├── recommendations/    # 여행지 추천 API
│   │   └── plans/              # 여행 일정 생성 API
│   ├── ai/
│   │   ├── llm.py              # LLM 호출 로직
│   │   ├── rag.py              # RAG 파이프라인
│   │   └── retriever.py        # 벡터 검색 및 데이터 조회
│   ├── scripts/
│   │   ├── build_place_vectors.py    # 여행지 임베딩 생성
│   │   └── build_behavior_vectors.py # 행동 패턴 임베딩 생성
│   ├── requirements.txt
│   └── manage.py
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하세요. `.env.example`을 참고하세요.

```bash
cp .env.example .env
```

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DJANGO_SECRET_KEY` | Django 시크릿 키 | `your-secret-key` |
| `DJANGO_DEBUG` | 디버그 모드 | `True` |
| `DJANGO_ALLOWED_HOSTS` | 허용 호스트 | `localhost,127.0.0.1,backend` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | CORS 허용 출처 | `http://localhost:5173` |
| `POSTGRES_DB` | DB 이름 | `skn25` |
| `POSTGRES_USER` | DB 사용자 | `skn25` |
| `POSTGRES_PASSWORD` | DB 비밀번호 | |
| `POSTGRES_HOST` | DB 호스트 | `db` (Docker), `localhost` (로컬) |
| `POSTGRES_PORT` | DB 포트 | `5432` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-...` |
| `VITE_API_URL` | 프론트엔드에서 사용하는 API URL | `http://localhost:8000` |

---

## 실행 방법

### Docker Compose (권장)

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 파일에 실제 값 입력

# 2. 컨테이너 빌드 및 실행
docker-compose up --build

# 3. 벡터 DB 초기화 (최초 1회)
docker-compose exec backend python scripts/build_place_vectors.py
docker-compose exec backend python scripts/build_behavior_vectors.py
```

| 서비스 | 주소 |
|--------|------|
| 프론트엔드 | http://localhost:5173 |
| 백엔드 API | http://localhost:8000 |

---

### 로컬 개발

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev        # 개발 서버 (HMR 지원)
npm run build      # 프로덕션 빌드
```

---

## API 엔드포인트

### 채팅 (`/api/chat/`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/chat/` | 메시지 전송 및 AI 응답 수신 |
| `POST` | `/api/chat/create/` | 새 채팅 세션 생성 |
| `POST` | `/api/chat/save/` | 메시지 저장 |
| `GET`  | `/api/chat/list/` | 채팅 세션 목록 조회 |
| `GET`  | `/api/chat/{chat_id}/` | 특정 세션의 대화 히스토리 조회 |
| `DELETE` | `/api/chat/{chat_id}/` | 채팅 세션 삭제 |

### 추천 (`/api/recommend/`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/recommend/` | 여행지 추천 (지역·카테고리·동행자 기반) |

### 일정 (`/api/plan`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/plan` | 다일 여행 일정 생성 |

---

## AI 파이프라인 구조

```
사용자 입력
    │
    ▼
쿼리 확장 / 카테고리 키워드 추출
    │
    ├─ 벡터 검색 (pgvector)
    │      ├─ travel_place_vectors (여행지 임베딩)
    │      └─ user_behavior_vectors (행동 패턴 임베딩)
    │
    ▼
컨텍스트 구성 (RAG)
    │
    ▼
GPT-4o-mini 응답 생성
    │
    ▼
결과 파싱 및 반환
```

---

## 팀원

| 이름 | 역할 |
|------|------|
| (팀원 정보를 여기에 추가하세요) | |

---

## 라이선스

본 프로젝트는 교육 목적으로 제작되었습니다.
