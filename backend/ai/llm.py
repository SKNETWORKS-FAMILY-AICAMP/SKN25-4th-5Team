from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langsmith import traceable
from langsmith.wrappers import wrap_openai
import os
import json
import re


# 모델
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


def get_chat_prompt_variant():
    return os.getenv("CHAT_PROMPT_VARIANT", "v1").strip().lower()

# 임베딩 함수 
@traceable(name="get_embedding", run_type="embedding")
def get_embedding(text):
    from openai import OpenAI
    client = wrap_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding


# category 여행지 추천 
@traceable(name="generate_category_response", run_type="llm")
def generate_category_response(req, docs, behavior_text):

    context = "\n".join([
        f"{i}. {d['title']} ({d['sido']} {d['sgg']})"
        for i, d in enumerate(docs)
    ])

    # 프롬프트 
    prompt = f"""
    너는 여행 추천 시스템이다.

    사용자 조건:
    - 목적지: {req.destination}
    - 이동 수단: {req.transportation}
    - 동행자: {req.companion}

    사용자와 유사한 여행 패턴:
    {behavior_text}

    아래 후보 중에서만 선택해서 추천해:

    {context}

    규칙:
    - 반드시 후보 번호(index)만 사용
    - 새로운 여행지 만들지 말 것
    - 관련된 여행 유형 작성할 것

    출력(JSON):

    [
      {{
        "index": 0,
        "tag": "활동 유형",
        "description": "추천 이유"
      }}
    ]
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content




@traceable(name="generate_plan_with_rag", run_type="llm")
def generate_plan_with_rag(req, data):

    behavior = data["behavior"]
    places = data["places"]
    days = req.days  # req에서 일수 받아오기

    # 행동 패턴 텍스트
    behavior_text = "\n".join([
        f"{b[2]} / 이동: {b[3]}"
        for b in behavior
    ])

    # 여행지 후보
    place_text = "\n".join([
        f"- {p[0]} ({p[1]} {p[2]}) [{p[3]}]"
        for p in places
    ])

    prompt = f"""
너는 여행 일정 플래너다.

조건:
- 출발지: {req.departure}
- 목적지: {req.destination}
- 이동 수단: {req.transportation}
- 여행 기간: {days}일 (반드시 1일차부터 {days}일차까지 작성)

사용자 행동 패턴:
{behavior_text}

추천 여행지:
{place_text}

규칙:
- 반드시 1일차부터 {days}일차까지 빠짐없이 작성하라
- 일정 도중에 귀가하거나 출발지로 돌아가는 내용을 포함하지 마라
- 추천 여행지를 {days}일에 걸쳐 고르게 배분하라
- JSON 형식으로 출력하지 마라
- "활동:" 같은 형식 사용하지 마라
- 간결한 여행 일정 문장으로 작성

출력 형식:

1일차
09:00 관덕정에서 산책하며 여행 시작
12:30 메타포에서 점심 식사
15:00 부용정에서 여유로운 휴식
18:00 사직단에서 저녁 산책

2일차
...

(반드시 {days}일차까지 작성 완료)
"""

    res = llm.invoke([HumanMessage(content=prompt)])
    return res.content



# LLM 응답 변환 
def parse_category_json(text):
    try:
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except:
        return []


# 채팅 응답 생성
@traceable(name="generate_chat_response", run_type="llm")
def generate_chat_response(message, docs, behavior_text="", history=None, selected_place=None, meta_chat=False):
    history = history or []
    history_text = "\n".join([
        f"{item.get('role', 'user')}: {item.get('content', '')}"
        for item in history[-6:]
    ])

    context = "\n".join([
        f"- {d['title']} ({d['sido_nm']} {d['sgg_nm']}) / {d['content_type_nm']}"
        for d in docs
    ])

    prompt = f"""
    너는 자연스럽게 대화하는 여행 챗봇이다.

    사용자 현재 질문:
    {message}

    이전 대화:
    {history_text}

    선택된 기준 여행지:
    {selected_place if selected_place else "없음"}

    검색된 여행지 후보:
    {context if context else "없음"}

    유사 행동 패턴:
    {behavior_text if behavior_text else "없음"}

    규칙:
    - 사용자가 기억 여부나 이전 대화를 물으면 짧고 자연스럽게 답해.
    - 다만 검색된 여행지 후보가 있고 사용자가 추천, 일정, 코스, 여행지 선택을 원하면 기억보다 추천을 우선해.
    - 추천이 꼭 필요할 때만 추천을 제안해.
    - 선택된 기준 여행지가 있으면 그 장소를 중심으로 답해.
    - 검색 결과에 없는 정보는 지어내지 마.
    - 말투는 친근하고 자연스럽게.
    """

    prompt_variant = get_chat_prompt_variant()

    if prompt_variant == "v2":
        prompt += """

    추가 규칙:
    - 사용자의 동행자, 분위기, 활동 목적 같은 조건을 먼저 반영해 답해.
    - 후보 여행지가 있으면 답변 첫 문장에서 질문 의도에 맞는 추천 방향을 짧게 요약해.
    - 후보 여행지 이름은 1~3개까지만 자연스럽게 언급해.
    - 근거가 약하거나 후보가 부족하면 모른다고 솔직히 말하고, 가능한 범위에서만 안내해.
    - 여행지 이름만 나열하지 말고 왜 어울리는지 한 문장씩 짧게 붙여.
    - 답변은 너무 길지 않게 3~5문장 안에서 마무리해.
        """
    elif prompt_variant == "v3":
        prompt += """

    추가 규칙:
    - 사용자의 질문을 먼저 한 문장으로 재해석한 뒤 답변을 시작해.
    - 검색된 후보 안에서만 추천하고, 후보 밖 정보는 절대 추측하지 마.
    - 추천이 어렵다면 부족한 조건이 무엇인지 짧게 설명해.
    - 답변 마지막 문장에는 다음 질문 예시를 한 개만 제안해.
        """

    if meta_chat:
        prompt += "\n- 이번 답변은 여행지 리스트를 억지로 만들지 말고 1~3문장으로 자연스럽게 답해."

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
