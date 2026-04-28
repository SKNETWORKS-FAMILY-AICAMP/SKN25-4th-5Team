from django.urls import path
from .views import chat_api, create_chat, save_message, chat_list, get_chat

urlpatterns = [
    path("", chat_api),
    path("create/", create_chat),
    path("save/", save_message),
    path("list/", chat_list),
    path("<int:chat_id>/", get_chat),
]
