from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ai.rag import chat_rag
from .models import ChatMessage, ChatSession

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


# 새 대화 생성
@api_view(['POST'])
def create_chat(request):
    title = request.data.get("message", "새 대화")[:20]

    chat = ChatSession.objects.create(title=title)

    return Response({"chat_id": chat.id})


# 메세지 저장
@api_view(['POST'])
def save_message(request):
    ChatMessage.objects.create(
        chat_id=request.data["chat_id"],
        role=request.data["role"],
        content=request.data["content"],
        places=request.data.get("places", [])
    )
    return Response({"status": "ok"})


# 대화 목록
@api_view(['GET'])
def chat_list(request):
    chats = ChatSession.objects.all().order_by("-created_at")

    return Response([
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
        }
        for c in chats
    ])


# 특정 대화 불러오기
@api_view(['GET'])
def get_chat(request, chat_id):
    messages = ChatMessage.objects.filter(chat_id=chat_id).order_by("created_at")

    return Response([
        {
            "role": m.role,
            "content": m.content,
            "places": m.places,
        }
        for m in messages
    ])
