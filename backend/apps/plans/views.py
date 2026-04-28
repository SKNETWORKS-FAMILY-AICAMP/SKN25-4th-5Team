from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ai.llm import generate_plan_with_rag
from ai.retriever import retrieve_plan
import re
from .serializers import PlanRequestSerializer


class SimpleReq:
    def __init__(self, departure, destination, transportation):
        self.departure = departure
        self.destination = destination
        self.transportation = transportation


def parse_plan_text(text, departure, destination, day_count, places):
    itinerary = []
    current_activities = []

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if re.match(r'\d+일차', line):
            if current_activities:
                itinerary.append({"activities": current_activities})
                current_activities = []
        else:
            match = re.match(r'(\d{1,2}:\d{2})\s+(.+)', line)
            if match:
                current_activities.append({
                    "time": match.group(1),
                    "name": match.group(2)
                })

    if current_activities:
        itinerary.append({"activities": current_activities})

    recommendations = [
        {
            "title": p[0],
            "location": f"{p[1]} {p[2]}",
            "description": p[3]
        }
        for p in places[:5]
    ]

    return {
        "departure": departure,
        "destination": destination,
        "day_count": day_count,
        "estimated_time": None,
        "itinerary": itinerary,
        "recommendations": recommendations
    }


class PlanView(APIView):
    def post(self, request):
        serializer = PlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        req = SimpleReq(
            departure=data["departure"],
            destination=data["destination"],
            transportation=data["transportation"],
        )
        day_count = data["day_count"]

        try:
            rag_data = retrieve_plan(req)
            plan_text = generate_plan_with_rag(req, rag_data)
            result = parse_plan_text(
                plan_text,
                req.departure,
                req.destination,
                day_count,
                rag_data["places"]
            )
            return Response(result)
        except Exception as e:
            return Response({"status": "error", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)