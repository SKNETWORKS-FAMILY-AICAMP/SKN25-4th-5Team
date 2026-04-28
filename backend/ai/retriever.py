import psycopg2
from ai.llm import get_embedding
import os
from functools import lru_cache

# DB
def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),  
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )

# 카테고리 여행지 추천
def retrieve_category(req):

    # embedding용 문장
    query_text = f"""
        {req.destination}에서 출발하는
        {req.purpose} 여행
        {req.companion}와 함께하는 여행
        {req.transportation} 이용
    """

    # 벡터 변환
    query_embedding = get_embedding(query_text)

    conn = get_connection()
    cur = conn.cursor()

    # 여행지 (결과 후보)
    cur.execute("""
        SELECT 
            title,
            sido_nm,
            content_type_nm,
            sgg_nm,
            source,
            embedding <-> %s::vector AS distance
        FROM travel_place_vectors
        WHERE content_type_nm = %s
        AND sido_nm = %s
        ORDER BY embedding <-> %s::vector
        LIMIT 20
    """, (query_embedding, req.purpose, req.destination, query_embedding))

    places = cur.fetchall()

    # 행동 패턴 
    cur.execute("""
        SELECT 
            trip_visit_sido,
            trip_visit_sigungu,
            travel_activity,
            companion_type
        FROM user_behavior_vectors
        WHERE trip_visit_sido = %s
        LIMIT 20
    """, (req.destination,))

    behavior = cur.fetchall()

    cur.close()
    conn.close()

    # 여행지 후보 dict 형태 변환
    place_results = [
        {
            "title": row[0],
            "sido": row[1],
            "type": row[2],
            "sgg": row[3],
            "source": row[4]
        }
        for row in places
    ]

    behavior_text = "\n".join([
        f"{row[0]} {row[1]}에서 {row[2]} 활동, 동행자: {row[3]}"
        for row in behavior
    ]) 

    # 결과 반환
    return {
        "places": place_results,
        "behavior_text": behavior_text
    }



def retrieve_plan(req):

    conn = get_connection()
    cur = conn.cursor()

    # 행동패턴 
    cur.execute("""
        SELECT 
            trip_visit_sido,
            trip_visit_sigungu,
            travel_activity,
            trip_transport_incity
        FROM user_behavior_vectors
        WHERE trip_visit_sido = %s
        LIMIT 5
    """, (req.destination,))

    behavior = cur.fetchall()

    #  여행지 후보 
    cur.execute("""
        SELECT 
            title,
            sido_nm,
            sgg_nm,
            content_type_nm
        FROM travel_place_vectors
        WHERE sido_nm = %s
        LIMIT 10
    """, (req.destination,))

    places = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "behavior": behavior,
        "places": places
    }


# 메타 질문 판별
def is_meta_chat(message):
    memory_markers = [
        "기억해",
        "기억나",
        "기억하지",
        "내가 했던 말",
        "아까 뭐",
        "뭐였지",
    ]
    recommendation_markers = [
        "추천",
        "여행지",
        "코스",
        "일정",
        "계획",
        "짜",
        "골라",
        "알려줘",
        "가고",
        "갈만한",
    ]

    if any(marker in message for marker in recommendation_markers):
        return False

    return any(marker in message for marker in memory_markers)


# 순번 여행지 추출
def extract_selected_place(message, history=None):
    history = history or []
    order_map = {
        0: ["1번째", "1번", "첫번째", "첫 번째", "첫째"],
        1: ["2번째", "2번", "두번째", "두 번째", "둘째"],
        2: ["3번째", "3번", "세번째", "세 번째", "셋째"],
        3: ["4번째", "4번", "네번째", "네 번째", "넷째"],
        4: ["5번째", "5번", "다섯번째", "다섯 번째", "다섯째"],
    }

    selected_index = None
    for index, patterns in order_map.items():
        if any(pattern in message for pattern in patterns):
            selected_index = index
            break

    if selected_index is None:
        return None

    for item in reversed(history or []):
        places = item.get("places") or []
        if places and len(places) > selected_index:
            return places[selected_index]
    return None


# 채팅 질의 확장
def build_chat_query(message, history=None):
    history = history or []
    follow_up_markers = [
        "그중",
        "그중에서",
        "거기",
        "거기서",
        "그거",
        "그곳",
        "그 코스",
        "그 일정",
        "다시",
        "그럼",
        "그러면",
        "이번엔",
    ]
    is_follow_up = any(marker in message for marker in follow_up_markers)
    is_short_message = len(message.strip()) <= 24

    recent_user_messages = []
    for item in reversed(history):
        if item.get("role") == "user":
            content = (item.get("content") or "").strip()
            if content:
                recent_user_messages.append(content)
        if len(recent_user_messages) >= 2:
            break

    if not recent_user_messages:
        return message

    if not is_follow_up and not is_short_message:
        last_user_message = recent_user_messages[0]
        if last_user_message == message:
            return message
        return " / ".join([last_user_message, message])

    recent_user_messages.reverse()
    merged = []
    for content in recent_user_messages + [message]:
        if content and (not merged or merged[-1] != content):
            merged.append(content)
    return " / ".join(merged)


@lru_cache(maxsize=1)
def get_content_types():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT content_type_nm
        FROM travel_place_vectors
        WHERE content_type_nm IS NOT NULL
    """)
    content_types = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return content_types


# DB에 적재된 카테고리명 기준으로만 카테고리 추출
def extract_category_keywords(message):
    return [
        content_type
        for content_type in get_content_types()
        if content_type and content_type in message
    ]


# 카테고리 가중치
def rerank_chat_places(places, message):
    preferred_categories = extract_category_keywords(message)
    if not preferred_categories:
        return places

    ranked = []
    for index, item in enumerate(places):
        score = 0
        content_type = item.get("content_type_nm", "")
        title = item.get("title", "")

        if content_type in preferred_categories:
            score += 3

        if title and any(category in title for category in preferred_categories):
            score += 1

        ranked.append((score, -index, item))

    ranked.sort(reverse=True)
    return [item for _, _, item in ranked]


def dedupe_places(places):
    seen = set()
    deduped = []

    for place in places:
        key = (
            place.get("title"),
            place.get("sido_nm"),
            place.get("sgg_nm"),
            place.get("content_type_nm"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(place)

    return deduped


@lru_cache(maxsize=1)
def get_regions():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT sido_nm FROM travel_place_vectors")
    regions = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return regions


def detect_region(message):
    regions = get_regions()
    for region in regions:
        if region in message:
            return region
    return None



# 채팅 검색 
def retrieve_chat(message, history=None, limit=5, region=None):
    resolved_query = build_chat_query(message, history)
    selected_place = extract_selected_place(message, history)
    meta_chat = is_meta_chat(message)

    conn = get_connection()
    cur = conn.cursor()

    places = []
    behavior_text = ""

    if not (meta_chat and selected_place is None):
        query_embedding = get_embedding(resolved_query)


        # 일반 후보 검색
        cur.execute("""
            SELECT 
                title,
                sido_nm,
                content_type_nm,
                sgg_nm,
                source,
                embedding <-> %s::vector AS distance
            FROM travel_place_vectors
            WHERE (%s IS NULL OR sido_nm = %s)
            ORDER BY embedding <-> %s::vector
            LIMIT %s
        """, (
            query_embedding,
            region,
            region,
            query_embedding,
            max(limit * 4, 20)
        ))

        rows = cur.fetchall()

        places = [
            {
                "title": row[0],
                "sido_nm": row[1],
                "content_type_nm": row[2],
                "sgg_nm": row[3],
                "source": row[4],
            }
            for row in rows
        ]
        places = dedupe_places(places)

        places = [
            p for p in places
            if not selected_place or p["title"] != selected_place.get("title")
        ]

        # rerank 

        places = rerank_chat_places(places, message)

     
        # 마지막에 limit
        places = places[:limit]

        # 행동 데이터
        cur.execute("""
            SELECT 
                trip_visit_sido,
                trip_visit_sigungu,
                travel_activity,
                companion_type
            FROM user_behavior_vectors
            ORDER BY embedding <-> %s::vector
            LIMIT 5
        """, (query_embedding,))

        behavior = cur.fetchall()

        behavior_text = "\n".join([
            f"{row[0]} {row[1]}에서 {row[2]} 활동, 동행자: {row[3]}"
            for row in behavior
        ])

    cur.close()
    conn.close()

    return {
        "resolved_query": resolved_query,
        "selected_place": selected_place,
        "show_places": bool(places) and not meta_chat,
        "places": places,
        "behavior_text": behavior_text,
        "meta_chat": meta_chat,
    }
