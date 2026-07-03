from django.db import models
from django.contrib.auth.models import AbstractUser
import random

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username


class Location(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    address = models.CharField(max_length=255)
    address_normalized = models.CharField(max_length=255, unique=True)
    lat = models.FloatField()
    lng = models.FloatField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    hint = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'locations'

    def __str__(self):
        return self.address


class GameSession(models.Model):
    MODE_CHOICES = [
        ('training', 'Тренировка'),
        ('exam', 'Экзамен'),
        ('sprint', 'Спринт'),
    ]
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('finished', 'Завершена'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='training')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    total_score = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'game_sessions'

    def __str__(self):
        return f'{self.user.username} — {self.mode} — {self.started_at}'


class Round(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='rounds')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='rounds')
    user_lat = models.FloatField()
    user_lng = models.FloatField()
    distance_meters = models.FloatField()
    time_seconds = models.FloatField()
    score = models.IntegerField(default=0)
    combo_multiplier = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rounds'

    def __str__(self):
        return f'Round {self.id} — {self.distance_meters}m — {self.score}pts'


class PlayerStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    total_rounds = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    avg_distance = models.FloatField(default=0)
    avg_time = models.FloatField(default=0)
    best_score = models.IntegerField(default=0)
    accuracy_rate = models.FloatField(default=0)
    current_streak = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'player_stats'

    def __str__(self):
        return f'{self.user.username} — stats'


class Leaderboard(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'День'),
        ('weekly', 'Неделя'),
        ('alltime', 'Всё время'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='alltime')
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    accuracy_rate = models.FloatField(default=0)
    avg_time = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leaderboard'
        unique_together = ('user', 'period')

    def __str__(self):
        return f'{self.user.username} — {self.period} — rank {self.rank}'
    

class TaskSet(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    locations = models.ManyToManyField(Location, related_name='task_sets', blank=True)
    difficulty = models.CharField(max_length=10, choices=Location.DIFFICULTY_CHOICES, default='easy')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_sets'

    def __str__(self):
        return self.name


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verifications'

    def generate_code(self):
        self.code = str(random.randint(100000, 999999))
        self.save()