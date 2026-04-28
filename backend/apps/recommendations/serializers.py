from rest_framework import serializers

class RecommendationRequestSerializer(serializers.Serializer):
    destination = serializers.CharField()
    purpose = serializers.CharField()
    transportation = serializers.CharField()
    companion = serializers.CharField(required=False, allow_blank=True)
    duration = serializers.IntegerField(required=False)