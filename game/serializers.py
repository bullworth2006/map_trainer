from rest_framework import serializers
from .models import Location, GameSession, Round, PlayerStats, Leaderboard


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'address', 'difficulty', 'hint']
        # lat и lng не отдаём — это правильный ответ, пользователь не должен его видеть


class RoundResultSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    location_id = serializers.IntegerField()
    user_lat = serializers.FloatField()
    user_lng = serializers.FloatField()
    time_seconds = serializers.FloatField()


class RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ['id', 'distance_meters', 'time_seconds', 'score', 'combo_multiplier']


class PlayerStatsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')

    class Meta:
        model = PlayerStats
        fields = ['username', 'total_rounds', 'avg_distance', 'avg_time', 'best_score', 'accuracy_rate']


class LeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')

    class Meta:
        model = Leaderboard
        fields = ['username', 'period', 'score', 'rank', 'accuracy_rate', 'avg_time']