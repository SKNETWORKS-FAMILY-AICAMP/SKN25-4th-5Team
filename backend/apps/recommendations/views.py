from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ai.rag import category_rag
from .serializers import RecommendationRequestSerializer


# Create your views here.
class Req:
    def __init__(self, data):
        self.destination = data.get("destination")
        self.purpose = data.get("purpose")
        self.companion = data.get("companion")
        self.transportation = data.get("transportation")


@api_view(['POST'])
def recommend_api(request):
    req = Req(request.data)   
    result = category_rag(req)
    return Response(result)


@api_view(['POST'])
def search_api(request):
    serializer = RecommendationRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    req = Req(serializer.validated_data)

    result = category_rag(req)
    items = result.get("items", [])

    return Response({
        "results": [
            {
                "title": item.get("title", ""),
                "location": item.get("region", ""),
                "content_type": item.get("tag", ""),
                "description": item.get("description", ""),
                "source": item.get("source", ""),
            }
            for item in items
        ]
    })