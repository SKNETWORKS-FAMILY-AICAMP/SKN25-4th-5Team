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


def normalize_text(value, default=""):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def build_embedding_text(row):
    return " | ".join(
        [
            f"source:{normalize_text(row[0], 'unknown')}",
            f"title:{normalize_text(row[1], 'unknown')}",
            f"category:{normalize_text(row[2], 'unknown')}",
            f"sido:{normalize_text(row[3], 'unknown')}",
            f"sgg:{normalize_text(row[4], 'unknown')}",
        ]
    )


def vector_literal(values):
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def create_vector_table(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(
            f"""
            DROP TABLE IF EXISTS travel_place_vectors;
            CREATE TABLE travel_place_vectors (
                source VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                content_type_nm VARCHAR(100),
                sido_nm VARCHAR(50),
                sgg_nm VARCHAR(50),
                embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    conn.commit()


def get_total_places(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    source,
                    title,
                    content_type_nm,
                    sido_nm,
                    sgg_nm
                FROM travel_places
            ) AS deduped_places;
            """
        )
        return cur.fetchone()[0]


def iter_places(conn, batch_size):
    with conn.cursor(name="travel_places_cursor") as cur:
        cur.itersize = batch_size
        cur.execute(
            """
            SELECT DISTINCT
                source,
                title,
                content_type_nm,
                sido_nm,
                sgg_nm
            FROM travel_places
            ORDER BY sido_nm, sgg_nm, title;
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
                normalize_text(row[0], "unknown")[:50],
                normalize_text(row[1], "unknown")[:255],
                normalize_text(row[2])[:100] or None,
                normalize_text(row[3])[:50] or None,
                normalize_text(row[4])[:50] or None,
                vector_literal(embedding),
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO travel_place_vectors (
                source,
                title,
                content_type_nm,
                sido_nm,
                sgg_nm,
                embedding
            ) VALUES %s
            """,
            values,
            template="(%s, %s, %s, %s, %s, %s::vector)",
            page_size=EMBEDDING_BATCH_SIZE,
        )
    conn.commit()


def create_vector_index(conn):
    with conn.cursor() as cur:
        cur.execute("SET maintenance_work_mem = '256MB';")
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS travel_place_vectors_embedding_idx
            ON travel_place_vectors
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """
        )
        cur.execute("ANALYZE travel_place_vectors;")
    conn.commit()


def build_place_vectors():
    embeddings_client = get_embeddings_client()
    read_conn = get_connection()
    write_conn = get_connection()
    try:
        create_vector_table(write_conn)
        total = get_total_places(read_conn)
        print(f"travel_places rows: {total}")

        if total == 0:
            print("벡터화할 travel_places 데이터가 없습니다.")
            return

        processed = 0
        for batch in iter_places(read_conn, EMBEDDING_BATCH_SIZE):
            texts = [build_embedding_text(row) for row in batch]
            vectors = embeddings_client.embed_documents(texts)
            insert_vectors(write_conn, batch, vectors)
            processed += len(batch)
            print(f"processed: {processed}/{total}")

        create_vector_index(write_conn)
        print("travel_place_vectors 테이블 생성 및 벡터 적재 완료")
    finally:
        read_conn.close()
        write_conn.close()


if __name__ == "__main__":
    build_place_vectors()
