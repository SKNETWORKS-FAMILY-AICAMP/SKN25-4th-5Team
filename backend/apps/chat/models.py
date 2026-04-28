from django.db import models

# Create your models here.
class ChatSession(models.Model):
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # user / assistant
    content = models.TextField()
    places = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
