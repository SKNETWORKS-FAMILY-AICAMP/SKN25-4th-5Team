from ai.retriever import retrieve_category, retrieve_chat, retrieve_plan
from ai.llm import (
    generate_category_response,
    parse_category_json,
    generate_chat_response,
    generate_plan_with_rag
)

# 카테고리 여행지 추천 
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
def chat_rag(message, history=None, limit=5):
    result = retrieve_chat(message=message, history=history, limit=limit)

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

    return {
        "answer": answer,
        "places": places,
        "show_places": result["show_places"],
        "resolved_query": result["resolved_query"],
    }

def plan_rag(req):

    data = retrieve_plan(req)

    result = generate_plan_with_rag(req, data)

    return result
