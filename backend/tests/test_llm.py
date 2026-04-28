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
