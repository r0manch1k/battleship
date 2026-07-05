from django.urls import path

from app.apps.game import views

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "leaderboard/",
        views.LeaderboardView.as_view(),
        name="leaderboard",
    ),
    path(
        "history/",
        views.HistoryView.as_view(),
        name="history",
    ),
    path(
        "new/",
        views.NewGameView.as_view(),
        name="new",
    ),
]
