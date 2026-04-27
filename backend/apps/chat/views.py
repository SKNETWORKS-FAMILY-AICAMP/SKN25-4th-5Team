from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ai.rag import chat_rag

# Create your views here.
@api_view(['POST'])
def chat_api(request):
    message = request.data.get("message")
    history = request.data.get("history", [])
    limit = request.data.get("limit", 5)

    result = chat_rag(
        message=message,
        history=history,
        limit=limit
    )

    return Response(result)