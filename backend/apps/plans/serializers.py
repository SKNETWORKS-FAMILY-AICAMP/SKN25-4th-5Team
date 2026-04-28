from rest_framework import serializers

class PlanRequestSerializer(serializers.Serializer):
    departure = serializers.CharField()
    destination = serializers.CharField()
    travel_type = serializers.CharField()
    transportation = serializers.CharField()
    departure_time = serializers.IntegerField(min_value=0, max_value=23)