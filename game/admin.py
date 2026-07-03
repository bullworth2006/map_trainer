from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Location, GameSession, Round, PlayerStats, Leaderboard, TaskSet
import csv
from django.http import HttpResponse


def export_rounds_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rounds_export.csv"'
    response.write('\ufeff')  # BOM для корректной кодировки в Excel

    writer = csv.writer(response)
    writer.writerow(['Игрок', 'Адрес', 'Расстояние (м)', 'Время (сек)', 'Очки', 'Дата'])

    for r in queryset:
        writer.writerow([
            r.session.user.username,
            r.location.address,
            round(r.distance_meters, 1),
            round(r.time_seconds, 1),
            r.score,
            r.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response

export_rounds_csv.short_description = "Экспортировать выбранные раунды в CSV"

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Роль', {'fields': ('role',)}),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['address', 'difficulty', 'is_active', 'created_at']
    list_filter = ['difficulty', 'is_active']
    search_fields = ['address']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'mode', 'difficulty', 'status', 'total_score', 'started_at']
    list_filter = ['mode', 'difficulty', 'status']


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ['session', 'location', 'distance_meters', 'time_seconds', 'score']
    actions = [export_rounds_csv]


@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_rounds', 'avg_distance', 'best_score', 'accuracy_rate']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'score', 'rank', 'updated_at']
    list_filter = ['period']

@admin.register(TaskSet)
class TaskSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'difficulty', 'is_active', 'created_at']
    list_filter = ['difficulty', 'is_active']
    filter_horizontal = ['locations']