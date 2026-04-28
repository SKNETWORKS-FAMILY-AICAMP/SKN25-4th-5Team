from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.chat.models import ChatMessage, ChatSession


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_chat_api_returns_rag_payload(api_client):
    mocked = {
        "answer": "서울숲과 북촌한옥마을을 추천할게요.",
        "places": [
            {"title": "서울숲"},
            {"title": "북촌한옥마을"},
        ],
        "show_places": True,
        "resolved_query": "서울 친구 조용한 여행",
    }

    with patch("apps.chat.views.chat_rag", return_value=mocked) as rag_mock:
        response = api_client.post(
            "/api/chat/",
            {
                "message": "서울에서 친구랑 갈 만한 조용한 여행지 추천해줘",
                "history": [],
                "limit": 3,
            },
            format="json",
        )

    assert response.status_code == 200
    assert response.json()["answer"] == mocked["answer"]
    rag_mock.assert_called_once()


@pytest.mark.django_db
def test_chat_session_crud_flow(api_client):
    create_response = api_client.post(
        "/api/chat/create/",
        {"message": "서울 여행 추천해줘"},
        format="json",
    )
    assert create_response.status_code == 200

    chat_id = create_response.json()["chat_id"]
    assert ChatSession.objects.filter(id=chat_id).exists()

    save_response = api_client.post(
        "/api/chat/save/",
        {
            "chat_id": chat_id,
            "role": "user",
            "content": "서울 여행 추천해줘",
            "places": [{"title": "서울숲"}],
        },
        format="json",
    )
    assert save_response.status_code == 200
    assert ChatMessage.objects.filter(chat_id=chat_id).count() == 1

    list_response = api_client.get("/api/chat/list/")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == chat_id

    detail_response = api_client.get(f"/api/chat/{chat_id}/")
    assert detail_response.status_code == 200
    assert detail_response.json()[0]["content"] == "서울 여행 추천해줘"

    delete_response = api_client.delete(f"/api/chat/{chat_id}/")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"
    assert not ChatSession.objects.filter(id=chat_id).exists()


@pytest.mark.django_db
def test_recommendation_search_transforms_items(api_client):
    mocked = {
        "items": [
            {
                "title": "경복궁",
                "region": "서울특별시 종로구",
                "tag": "역사 유적지 방문",
                "source": "tourapi",
                "description": "부모님과 함께 둘러보기 좋은 궁궐입니다.",
            }
        ]
    }

    with patch("apps.recommendations.views.category_rag", return_value=mocked):
        response = api_client.post(
            "/api/recommend/",
            {
                "destination": "서울특별시",
                "purpose": "관광지",
                "transportation": "도보",
                "companion": "부모",
            },
            format="json",
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["title"] == "경복궁"
    assert payload["results"][0]["location"] == "서울특별시 종로구"


@pytest.mark.django_db
def test_recommendation_search_validates_required_fields(api_client):
    response = api_client.post(
        "/api/recommend/",
        {
            "destination": "서울특별시",
            "transportation": "도보",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "purpose" in response.json()


@pytest.mark.django_db
def test_plan_api_returns_parsed_itinerary(api_client):
    rag_data = {
        "behavior": [("서울", "종로구", "역사 유적지 방문", "도보")],
        "places": [
            ("경복궁", "서울특별시", "종로구", "관광지"),
            ("북촌한옥마을", "서울특별시", "종로구", "관광지"),
        ],
    }
    plan_text = "\n".join(
        [
            "1일차",
            "09:00 경복궁 관람",
            "13:00 북촌한옥마을 산책",
        ]
    )

    with patch("apps.plans.views.retrieve_plan", return_value=rag_data), patch(
        "apps.plans.views.generate_plan_with_rag",
        return_value=plan_text,
    ):
        response = api_client.post(
            "/api/plan",
            {
                "departure": "서울특별시",
                "destination": "서울특별시",
                "travel_type": "역사 유적지 방문",
                "transportation": "도보",
                "departure_hour": 9,
                "day_count": 1,
            },
            format="json",
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["departure"] == "서울특별시"
    assert payload["day_count"] == 1
    assert payload["itinerary"][0]["activities"][0]["name"] == "경복궁 관람"
    assert payload["recommendations"][0]["title"] == "경복궁"
