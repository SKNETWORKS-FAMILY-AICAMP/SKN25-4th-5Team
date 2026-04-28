import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from psycopg2.extras import execute_values

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))

SELECTED_COLUMNS = [
    "with_pet",
    "gender",
    "age_group",
    "companion_type",
    "trip_transport_city2city",
    "trip_transport_incity",
    "travel_activity",
    "trip_visit_sido",
    "trip_visit_sigungu",
]


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def get_embeddings_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=api_key)


def normalize_text(value, default="N"):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def build_embedding_text(row):
    return " | ".join(
        [
            f"with_pet:{normalize_text(row[0])}",
            f"gender:{normalize_text(row[1])}",
            f"age_group:{normalize_text(row[2])}",
            f"companion_type:{normalize_text(row[3])}",
            f"transport_city2city:{normalize_text(row[4])}",
            f"transport_incity:{normalize_text(row[5])}",
            f"travel_activity:{normalize_text(row[6])}",
            f"visit_sido:{normalize_text(row[7])}",
            f"visit_sigungu:{normalize_text(row[8])}",
        ]
    )


def vector_literal(values):
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def create_vector_table(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(
            f"""
            DROP TABLE IF EXISTS user_behavior_vectors;
            CREATE TABLE user_behavior_vectors (
                with_pet VARCHAR(20),
                gender VARCHAR(20),
                age_group VARCHAR(20),
                companion_type VARCHAR(100),
                trip_transport_city2city VARCHAR(50),
                trip_transport_incity VARCHAR(50),
                travel_activity TEXT,
                trip_visit_sido VARCHAR(50),
                trip_visit_sigungu VARCHAR(50),
                embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    conn.commit()


def get_total_behaviors(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    with_pet,
                    gender,
                    age_group,
                    companion_type,
                    trip_transport_city2city,
                    trip_transport_incity,
                    travel_activity,
                    trip_visit_sido,
                    trip_visit_sigungu
                FROM user_behavior
            ) AS deduped_behavior;
            """
        )
        return cur.fetchone()[0]


def iter_behaviors(conn, batch_size):
    with conn.cursor(name="user_behavior_cursor") as cur:
        cur.itersize = batch_size
        cur.execute(
            """
            SELECT DISTINCT
                with_pet,
                gender,
                age_group,
                companion_type,
                trip_transport_city2city,
                trip_transport_incity,
                travel_activity,
                trip_visit_sido,
                trip_visit_sigungu
            FROM user_behavior
            ORDER BY trip_visit_sido, trip_visit_sigungu, age_group, companion_type;
            """
        )
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            yield rows


def insert_vectors(conn, rows, embeddings):
    values = []
    for row, embedding in zip(rows, embeddings):
        values.append(
            (
                normalize_text(row[0])[:20],
                normalize_text(row[1])[:20],
                normalize_text(row[2])[:20],
                normalize_text(row[3])[:100],
                normalize_text(row[4])[:50],
                normalize_text(row[5])[:50],
                normalize_text(row[6]),
                normalize_text(row[7])[:50],
                normalize_text(row[8])[:50],
                vector_literal(embedding),
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO user_behavior_vectors (
                with_pet,
                gender,
                age_group,
                companion_type,
                trip_transport_city2city,
                trip_transport_incity,
                travel_activity,
                trip_visit_sido,
                trip_visit_sigungu,
                embedding
            ) VALUES %s
            """,
            values,
            template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)",
            page_size=EMBEDDING_BATCH_SIZE,
        )
    conn.commit()


def create_vector_index(conn):
    with conn.cursor() as cur:
        cur.execute("SET maintenance_work_mem = '256MB';")
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS user_behavior_vectors_embedding_idx
            ON user_behavior_vectors
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """
        )
        cur.execute("ANALYZE user_behavior_vectors;")
    conn.commit()


def build_behavior_vectors():
    embeddings_client = get_embeddings_client()
    read_conn = get_connection()
    write_conn = get_connection()
    try:
        create_vector_table(write_conn)
        total = get_total_behaviors(read_conn)
        print(f"user_behavior rows: {total}")

        if total == 0:
            print("벡터화할 user_behavior 데이터가 없습니다.")
            return

        processed = 0
        for batch in iter_behaviors(read_conn, EMBEDDING_BATCH_SIZE):
            texts = [build_embedding_text(row) for row in batch]
            vectors = embeddings_client.embed_documents(texts)
            insert_vectors(write_conn, batch, vectors)
            processed += len(batch)
            print(f"processed: {processed}/{total}")

        create_vector_index(write_conn)
        print("user_behavior_vectors 테이블 생성 및 벡터 적재 완료")
    finally:
        read_conn.close()
        write_conn.close()


if __name__ == "__main__":
    build_behavior_vectors()
