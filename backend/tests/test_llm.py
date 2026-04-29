from unittest.mock import patch

import ai.llm as llm_module
from ai.llm import generate_chat_response, parse_category_json


def test_parse_category_json_handles_markdown_code_fences():
    raw = """```json
    [
      {"index": 0, "tag": "관광지", "description": "추천 이유"}
    ]
    ```"""

    parsed = parse_category_json(raw)

    assert parsed[0]["index"] == 0
    assert parsed[0]["tag"] == "관광지"


def test_generate_chat_response_applies_prompt_variant_v2(monkeypatch):
    captured = {}

    class DummyResponse:
        content = "테스트 응답"

    class DummyLLM:
        def invoke(self, messages):
            captured["prompt"] = messages[0].content
            return DummyResponse()

    monkeypatch.setenv("CHAT_PROMPT_VARIANT", "v2")
    monkeypatch.setattr(llm_module, "llm", DummyLLM())

    response = generate_chat_response(
        message="서울에서 친구랑 갈 만한 조용한 여행지 추천해줘",
        docs=[
            {
                "title": "서울숲",
                "sido_nm": "서울특별시",
                "sgg_nm": "성동구",
                "content_type_nm": "관광지",
            }
        ],
        behavior_text="서울 성동구에서 산책 활동, 동행자: 친구",
        history=[],
        selected_place=None,
        meta_chat=False,
    )

    assert response == "테스트 응답"
    assert "사용자의 동행자, 분위기, 활동 목적 같은 조건을 먼저 반영해 답해." in captured["prompt"]
    assert "3~5문장 안에서 마무리해." in captured["prompt"]


def test_generate_chat_response_adds_meta_chat_rule():
    captured = {}

    class DummyResponse:
        content = "메타 응답"

    class DummyLLM:
        def invoke(self, messages):
            captured["prompt"] = messages[0].content
            return DummyResponse()

    with patch.object(llm_module, "llm", DummyLLM()):
        response = generate_chat_response(
            message="내가 아까 뭐 물어봤는지 기억해?",
            docs=[],
            behavior_text="",
            history=[],
            selected_place=None,
            meta_chat=True,
        )

    assert response == "메타 응답"
    assert "1~3문장으로 자연스럽게 답해." in captured["prompt"]


def test_generate_chat_response_applies_prompt_variant_v4_and_shorter_history(monkeypatch):
    captured = {}

    class DummyResponse:
        content = "속도 최적화 응답"

    class DummyLLM:
        def invoke(self, messages):
            captured["prompt"] = messages[0].content
            return DummyResponse()

    history = [
        {"role": "user", "content": "첫 번째 질문"},
        {"role": "assistant", "content": "첫 번째 답변"},
        {"role": "user", "content": "두 번째 질문"},
        {"role": "assistant", "content": "두 번째 답변"},
        {"role": "user", "content": "세 번째 질문"},
    ]

    monkeypatch.setenv("CHAT_PROMPT_VARIANT", "v4")
    monkeypatch.delenv("CHAT_HISTORY_LIMIT", raising=False)
    monkeypatch.setattr(llm_module, "llm", DummyLLM())

    response = generate_chat_response(
        message="서울에서 부모님과 갈 조용한 여행지 알려줘",
        docs=[
            {
                "title": "창덕궁",
                "sido_nm": "서울특별시",
                "sgg_nm": "종로구",
                "content_type_nm": "관광지",
            }
        ],
        history=history,
        selected_place=None,
        meta_chat=False,
    )

    assert response == "속도 최적화 응답"
    assert "답변은 2~4문장 안에서 끝내고" in captured["prompt"]
    assert "추가 질문 예시는 붙이지 마." in captured["prompt"]
    assert "첫 번째 질문" not in captured["prompt"]
    assert "첫 번째 답변" not in captured["prompt"]
    assert "두 번째 질문" in captured["prompt"]
    assert "두 번째 답변" in captured["prompt"]
    assert "세 번째 질문" in captured["prompt"]


def test_generate_chat_response_applies_prompt_variant_v5(monkeypatch):
    captured = {}

    class DummyResponse:
        content = "품질 강화 응답"

    class DummyLLM:
        def invoke(self, messages):
            captured["prompt"] = messages[0].content
            return DummyResponse()

    monkeypatch.setenv("CHAT_PROMPT_VARIANT", "v5")
    monkeypatch.setattr(llm_module, "llm", DummyLLM())

    response = generate_chat_response(
        message="서울에서 부모님과 함께 조용하게 둘러볼 만한 곳 추천해줘",
        docs=[
            {
                "title": "창덕궁",
                "sido_nm": "서울특별시",
                "sgg_nm": "종로구",
                "content_type_nm": "관광지",
            },
            {
                "title": "덕수궁",
                "sido_nm": "서울특별시",
                "sgg_nm": "중구",
                "content_type_nm": "관광지",
            },
        ],
        behavior_text="부모님 동반, 조용한 산책 선호",
        history=[],
        selected_place=None,
        meta_chat=False,
    )

    assert response == "품질 강화 응답"
    assert "각 장소마다 사용자 조건에 맞는 이유를 아주 구체적으로 짧게 붙여." in captured["prompt"]
    assert "여러 장소를 추천할 때는 서로 어떻게 다른지 비교가 되게 설명해." in captured["prompt"]
    assert "답변은 4~6문장 안에서 충분히 친절하게 마무리해." in captured["prompt"]


def test_generate_chat_response_applies_prompt_variant_v6(monkeypatch):
    captured = {}

    class DummyResponse:
        content = "v6 응답"

    class DummyLLM:
        def invoke(self, messages):
            captured["prompt"] = messages[0].content
            return DummyResponse()

    monkeypatch.setenv("CHAT_PROMPT_VARIANT", "v6")
    monkeypatch.setattr(llm_module, "llm", DummyLLM())

    response = generate_chat_response(
        message="서울에서 친구랑 조용하게 산책할 만한 곳 추천해줘",
        docs=[
            {
                "title": "서울숲",
                "sido_nm": "서울특별시",
                "sgg_nm": "성동구",
                "content_type_nm": "관광지",
            }
        ],
        behavior_text="친구와 산책 선호",
        history=[],
        selected_place=None,
        meta_chat=False,
    )

    assert response == "v6 응답"
    assert "동행자, 분위기, 활동 목적처럼 질문과 직접 연결된 조건을 우선 반영해." in captured["prompt"]
    assert "왜 어울리는지 짧게 설명해." in captured["prompt"]
    assert "선택 기준이나 다음 질문을 짧게 한 문장 제안해." in captured["prompt"]
