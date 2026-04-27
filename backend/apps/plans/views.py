from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
from .serializers import PlanRequestSerializer

llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ.get("OPENAI_API_KEY"))

class PlanView(APIView):
    def post(self, request):
        serializer = PlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        departure = data["departure"]
        destination = data["destination"]
        travel_type = data["travel_type"]
        transportation = data["transportation"]
        departure_time = data["departure_time"]

        prompt = f"""
당신은 여행 일정 전문가입니다.
아래 조건을 바탕으로 하루 여행 일정을 시간대별로 작성해주세요.

- 출발지: {departure}
- 도착지: {destination}
- 여행 유형: {travel_type}
- 이동 수단: {transportation}
- 출발 시간: {departure_time}시

1일차 형식으로 시간대별 일정을 작성해주세요.
"""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            result = response.content
            return Response({"result": result})
        except Exception as e:
            return Response({"status": "error", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)