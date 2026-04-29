import os
import sys
from typing import Any
from pathlib import Path

from langsmith import Client, evaluate
from langchain_openai import ChatOpenAI

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.rag import chat_rag


DATASET_NAME = os.getenv("LANGSMITH_CHAT_DATASET", "skn25-chat-eval")
EXPERIMENT_PREFIX = os.getenv("LANGSMITH_CHAT_EXPERIMENT", "chat-rag-baseline")
PROMPT_VARIANT = os.getenv("CHAT_PROMPT_VARIANT", "v1")
MAX_CONCURRENCY = int(os.getenv("LANGSMITH_EVAL_CONCURRENCY", "1"))


judge_llm = ChatOpenAI(
    model=os.getenv("LANGSMITH_EVAL_MODEL", "gpt-4o-mini"),
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)


def chat_app(inputs: dict[str, Any]) -> dict[str, Any]:
    result = chat_rag(
        message=inputs["question"],
        history=inputs.get("history", []),
        limit=inputs.get("limit", 3),
    )
    return {
        "answer": result.get("answer", ""),
        "places": result.get("places", []),
        "place_titles": [p.get("title", "") for p in result.get("places", [])],
    }


def answer_exists(outputs: dict[str, Any]) -> bool:
    return bool(outputs.get("answer", "").strip())


def place_count_ok(outputs: dict[str, Any]) -> bool:
    return len(outputs.get("place_titles", [])) <= 3


def expected_keywords_match(outputs: dict[str, Any], reference_outputs: dict[str, Any]) -> float:
    answer = outputs.get("answer", "")
    keywords = reference_outputs.get("expected_keywords", [])
    if not keywords:
        return 1.0
    matched = sum(1 for keyword in keywords if keyword in answer)
    return matched / len(keywords)


def forbidden_keywords_absent(outputs: dict[str, Any], reference_outputs: dict[str, Any]) -> bool:
    answer = outputs.get("answer", "")
    forbidden = reference_outputs.get("forbidden_keywords", [])
    return not any(keyword and keyword in answer for keyword in forbidden)


def llm_relevance_judge(
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    reference_outputs: dict[str, Any],
) -> dict[str, Any]:
    prompt = f"""
당신은 여행 RAG 챗봇 평가자다.

사용자 질문:
{inputs.get("question", "")}

챗봇 답변:
{outputs.get("answer", "")}

답변에 기대하는 핵심 키워드:
{", ".join(reference_outputs.get("expected_keywords", []))}

평가 기준:
- 질문 의도와 관련이 있는가
- 여행 추천/안내 답변으로 자연스러운가
- 핵심 키워드를 어느 정도 반영했는가

반드시 아래 JSON 형식으로만 답하라:
{{
  "score": 1부터 5 사이 정수,
  "reason": "짧은 한국어 평가"
}}
"""
    response = judge_llm.invoke(prompt).content

    score = 1
    reason = response

    try:
        import json
        parsed = json.loads(response)
        score = int(parsed.get("score", 1))
        reason = parsed.get("reason", response)
    except Exception:
        pass

    return {
        "key": "llm_relevance_judge",
        "score": max(1, min(score, 5)),
        "comment": reason,
    }


def main():
    client = Client()
    client.read_dataset(dataset_name=DATASET_NAME)

    results = evaluate(
        chat_app,
        data=DATASET_NAME,
        evaluators=[
            answer_exists,
            place_count_ok,
            expected_keywords_match,
            forbidden_keywords_absent,
            llm_relevance_judge,
        ],
        experiment_prefix=EXPERIMENT_PREFIX,
        description=f"SKN25 chat RAG evaluation ({PROMPT_VARIANT})",
        max_concurrency=MAX_CONCURRENCY,
    )

    print("EVAL_DONE")
    experiment_name = getattr(results, "experiment_name", None) or getattr(results, "experiment", None)
    print(f"EXPERIMENT_NAME {experiment_name}")
    print(f"DATASET_NAME {DATASET_NAME}")


if __name__ == "__main__":
    main()
