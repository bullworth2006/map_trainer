from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from geopy.distance import geodesic
import random
from django.db.models import F
from .models import Location, GameSession, Round, PlayerStats, Leaderboard
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .serializers import (
    LocationSerializer, RoundResultSerializer,
    RoundSerializer, PlayerStatsSerializer, LeaderboardSerializer
)


@login_required
def game_page(request):
    return render(request, 'game/index.html')

@login_required
def stats_page(request):
    return render(request, 'game/stats.html')


@login_required
def leaderboard_page(request):
    return render(request, 'game/leaderboard.html')

@login_required
def setup_page(request):
    return render(request, 'game/setup.html')

def calculate_score(distance_meters, time_seconds, combo_multiplier):
    if distance_meters <= 5:
        base_score = 100
    elif distance_meters <= 20:
        base_score = 70
    elif distance_meters <= 50:
        base_score = 40
    else:
        base_score = 0

    # бонус за скорость
    if time_seconds <= 10:
        time_bonus = 50
    elif time_seconds <= 20:
        time_bonus = 30
    elif time_seconds <= 30:
        time_bonus = 10
    else:
        time_bonus = 0

    return int((base_score + time_bonus) * combo_multiplier)


def update_player_stats(user, distance, time_seconds, score):
    stats, created = PlayerStats.objects.get_or_create(user=user)

    total = stats.total_rounds
    stats.avg_distance = (stats.avg_distance * total + distance) / (total + 1)
    stats.avg_time = (stats.avg_time * total + time_seconds) / (total + 1)
    stats.total_rounds += 1

    if score > stats.best_score:
        stats.best_score = score

    accurate = Round.objects.filter(
        session__user=user,
        distance_meters__lte=50
    ).count()
    stats.accuracy_rate = (accurate / stats.total_rounds) * 100

    if distance <= 50:
        stats.current_streak += 1
        if stats.current_streak > stats.max_streak:
            stats.max_streak = stats.current_streak
    else:
        stats.current_streak = 0

    stats.save()


def update_leaderboard(user):
    stats = PlayerStats.objects.get(user=user)

    for period in ['daily', 'weekly', 'alltime']:
        lb, created = Leaderboard.objects.get_or_create(user=user, period=period)
        lb.score = stats.best_score
        lb.accuracy_rate = stats.accuracy_rate
        lb.avg_time = stats.avg_time
        lb.save()

    # пересчитываем ранги
    for period in ['daily', 'weekly', 'alltime']:
        entries = Leaderboard.objects.filter(period=period).order_by('-score')
        for i, entry in enumerate(entries, start=1):
            entry.rank = i
            entry.save()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request):
    mode = request.data.get('mode', 'training')
    difficulty = request.data.get('difficulty', 'easy')

    session = GameSession.objects.create(
        user=request.user,
        mode=mode,
        difficulty=difficulty,
    )
    return Response({'session_id': session.id}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_location(request):
    difficulty = request.query_params.get('difficulty', 'easy')
    exclude_id = request.query_params.get('exclude_id')

    locations = Location.objects.filter(difficulty=difficulty, is_active=True)

    if exclude_id and locations.count() > 1:
        locations = locations.exclude(id=exclude_id)

    if not locations.exists():
        return Response({'error': 'Нет доступных локаций'}, status=status.HTTP_404_NOT_FOUND)

    location = random.choice(list(locations))
    serializer = LocationSerializer(location)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    serializer = RoundResultSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    session = GameSession.objects.get(id=data['session_id'], user=request.user)
    location = Location.objects.get(id=data['location_id'])

    # считаем расстояние
    distance = geodesic(
        (location.lat, location.lng),
        (data['user_lat'], data['user_lng'])
    ).meters

    # считаем комбо
    last_rounds = Round.objects.filter(session=session).order_by('-created_at')[:3]
    combo = 1.0
    if len(last_rounds) >= 3 and all(r.distance_meters <= 50 for r in last_rounds):
        combo = 1.5

    score = calculate_score(distance, data['time_seconds'], combo)

    round_obj = Round.objects.create(
        session=session,
        location=location,
        user_lat=data['user_lat'],
        user_lng=data['user_lng'],
        distance_meters=distance,
        time_seconds=data['time_seconds'],
        score=score,
        combo_multiplier=combo,
    )

    session.total_score += score
    session.total_rounds += 1
    session.save()

    update_player_stats(request.user, distance, data['time_seconds'], score)
    update_leaderboard(request.user)

    return Response({
        'distance_meters': round(distance, 1),
        'score': score,
        'combo_multiplier': combo,
        'correct_lat': location.lat,
        'correct_lng': location.lng,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_session(request):
    session_id = request.data.get('session_id')
    session = GameSession.objects.get(id=session_id, user=request.user)
    session.status = 'finished'
    session.finished_at = timezone.now()
    session.save()

    PlayerStats.objects.filter(user=request.user).update(total_sessions=F('total_sessions') + 1)

    return Response({'total_score': session.total_score, 'total_rounds': session.total_rounds})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stats(request):
    stats = PlayerStats.objects.get(user=request.user)
    serializer = PlayerStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leaderboard(request):
    period = request.query_params.get('period', 'alltime')
    entries = Leaderboard.objects.filter(period=period).order_by('rank')[:20]
    serializer = LeaderboardSerializer(entries, many=True)
    return Response(serializer.data)