from django.shortcuts import render
from django.views.generic import TemplateView


def index(request):
    return render(request, "game/base.html")


class LeaderboardView(TemplateView):
    template_name = "game/leaderboard.html"


class HistoryView(TemplateView):
    template_name = "game/history.html"


class NewGameView(TemplateView):
    template_name = "game/new_game.html"
