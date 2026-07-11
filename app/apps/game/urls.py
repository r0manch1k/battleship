from django.urls import path

from app.apps.game import views

urlpatterns = [
    path("", views.index, name="index"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("history/", views.history, name="history"),
    path("new/", views.new, name="new"),
    path("<int:pk>/", views.game_detail, name="game_detail"),
    path("<int:pk>/shoot/", views.shoot, name="shoot"),
]
