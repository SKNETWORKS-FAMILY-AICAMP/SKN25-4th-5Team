from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
import json
import re


# 모델
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# 임베딩 함수 
def get_embedding(text):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding


# category 여행지 추천 
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




def generate_plan_with_rag(req, data):

    behavior = data["behavior"]
    places = data["places"]

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

사용자 행동 패턴:
{behavior_text}

추천 여행지:
{place_text}

규칙:
- JSON 형식으로 출력하지 마라
- "활동:" 같은 형식 사용하지 마라
- 자연스러운 여행 일정 문장으로 작성
- 사람이 여행 계획 짜듯이 작성

출력 형식:

1일차
09:00 관덕정에서 산책하며 여행 시작
12:30 메타포에서 점심 식사
15:00 부용정에서 여유로운 휴식
18:00 사직단에서 저녁 산책

2일차
...


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
        너는 여행 추천 전문가 챗봇이다.

        사용자 질문:
        {message}

        이전 대화:
        {history_text}

        검색된 여행지 후보:
        {context if context else "없음"}

        유사 행동 패턴:
        {behavior_text if behavior_text else "없음"}

        ---

        목표:
        사용자의 조건에 맞는 여행지를 최대 3개 추천하고, 각 장소를 구체적으로 설명한다.

        ---

        필수 규칙:

        1. 반드시 위 후보 리스트에서만 선택
        2. 사용자 조건과 맞지 않는 장소는 절대 선택하지 마
        (예: 반려동물인데 실내 쇼핑몰, 학교, 공공기관 ❌)
        3. 조건과 맞는 장소가 없으면 "조건에 맞는 여행지가 없습니다"라고 말해
        4. 절대 없는 장소를 만들지 마
        5. 추천 장소에 같은 장소 반복하지 마

        ---

        추천 기준:

        - 반려동물 → 산책 가능 / 야외 / 동반 가능 장소만
        - 레포츠 → 액티비티, 체험 중심
        - 관광 → 명소, 자연경관
        - 지역 → 해당 지역만

        ---

        출력 형식 (무조건 지켜):

        1. 장소명 (지역)
        - 왜 추천하는지 (사용자 조건 기반)
        - 어떤 경험을 할 수 있는지
        - 어떤 사람에게 좋은지

        2. 장소명 (지역)
        - 동일 형식

        (최대 3개)

        ---

        스타일:

        - 자연스럽고 친근하게
        - 불필요한 설명 없이 핵심만
        - "이곳은~" 같은 반복 표현 줄이기
    """

    if meta_chat:
        prompt += "\n- 이번 답변은 여행지 리스트를 억지로 만들지 마. 정말 필요한 경우에만 후보에서 선택해서 추천해."

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
    
