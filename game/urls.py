from django.urls import path
from . import views

urlpatterns = [
    path('', views.setup_page, name='setup_page'),
    path('play/', views.game_page, name='game_page'),
    path('stats/', views.stats_page, name='stats_page'),
    path('leaderboard/', views.leaderboard_page, name='leaderboard_page'),
    path('api/session/start/', views.start_session, name='start_session'),
    path('api/session/finish/', views.finish_session, name='finish_session'),
    path('api/location/', views.get_location, name='get_location'),
    path('api/answer/', views.submit_answer, name='submit_answer'),
    path('api/stats/', views.get_stats, name='get_stats'),
    path('api/leaderboard/', views.get_leaderboard, name='get_leaderboard'),
]