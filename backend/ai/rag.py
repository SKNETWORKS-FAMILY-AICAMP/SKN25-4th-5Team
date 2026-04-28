from ai.retriever import retrieve_category, retrieve_chat, retrieve_plan, get_regions
from ai.llm import (
    generate_category_response,
    parse_category_json,
    generate_chat_response,
    generate_plan_with_rag
)
from langsmith import traceable

# 카테고리 여행지 추천
@traceable(name="category_rag", run_type="chain")
def category_rag(req):
    # 후보 여행지 + 행동 패턴
    result = retrieve_category(req)

    places = result["places"]
    behavior_text = result["behavior_text"]

    raw = generate_category_response(req, places, behavior_text)

    # llm 응답 리스트 변환
    parsed = parse_category_json(raw)

    final = []

    # index 기반 실제 여행지 매칭
    for item in parsed:
        idx = item.get("index")

        if idx is not None and idx < len(places):
            final.append({
                "title": places[idx]["title"],
                "region": f"{places[idx]['sido']} {places[idx]['sgg']}",
                "tag": item.get("tag", ""),
                "source": places[idx]["source"],
                "description": item.get("description", "")
            })

    # 최종 결과 반환
    return {
        "items": final,
        "raw": raw
    }


# 채팅 RAG
@traceable(name="chat_rag", run_type="chain")
def chat_rag(message, history=None, limit=5):
    region = detect_region(message)

    result = retrieve_chat(
        message=message,
        history=history,
        limit=limit,
        region=region
    )

    places = result["places"]
    behavior_text = result["behavior_text"]

    answer = generate_chat_response(
        message=message,
        docs=places,
        behavior_text=behavior_text,
        history=history or [],
        selected_place=result["selected_place"],
        meta_chat=result["meta_chat"],
    )

    places = select_answer_places(answer, places, max_items=limit)

    return {
        "answer": answer,
        "places": places,
        "show_places": result["show_places"],
        "resolved_query": result["resolved_query"],
    }


@traceable(name="select_answer_places", run_type="tool")
def select_answer_places(answer, places, max_items=5):
    ordered = reorder_places(answer, dedupe_places(places))
    mentioned = [place for place in ordered if place["title"] in answer]

    if mentioned:
        return mentioned[:max_items]

    if "조건에 맞는 여행지가 없습니다" in answer:
        return []

    return ordered[:min(3, max_items)]


@traceable(name="dedupe_places", run_type="tool")
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


@traceable(name="reorder_places", run_type="tool")
def reorder_places(answer, places):
    mentioned = []
    not_mentioned = []

    for p in places:
        if p["title"] in answer:
            mentioned.append((answer.find(p["title"]), p))
        else:
            not_mentioned.append(p)

    mentioned.sort(key=lambda x: x[0])
    ordered = [p for _, p in mentioned] + not_mentioned

    return ordered


@traceable(name="plan_rag", run_type="chain")
def plan_rag(req):

    data = retrieve_plan(req)

    result = generate_plan_with_rag(req, data)

    return result


# 지역 감지(챗봇)
def detect_region(message):
    regions = get_regions()
    for r in regions:
        if r in message:
            return r
    return None
