from ai.retriever import extract_preference_signals, rerank_chat_places


def test_extract_preference_signals_detects_quiet_and_nature():
    signals = extract_preference_signals("서울에서 조용하게 자연 풍경 보면서 산책할 곳 추천해줘")

    assert "quiet" in signals
    assert "nature" in signals


def test_rerank_chat_places_prioritizes_places_matching_message_intent():
    places = [
        {
            "title": "시티몰",
            "sido_nm": "서울특별시",
            "sgg_nm": "중구",
            "content_type_nm": "쇼핑",
        },
        {
            "title": "서울숲",
            "sido_nm": "서울특별시",
            "sgg_nm": "성동구",
            "content_type_nm": "관광지",
        },
        {
            "title": "국립미술관",
            "sido_nm": "서울특별시",
            "sgg_nm": "종로구",
            "content_type_nm": "문화시설",
        },
    ]

    ranked = rerank_chat_places(
        places,
        "서울에서 전시나 박물관처럼 실내 문화시설 추천해줘",
    )

    assert ranked[0]["title"] == "국립미술관"
