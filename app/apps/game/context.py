from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from app.apps.game.models import Game


def sidebar(request):
    nusers = get_user_model().objects.count()
    ngames = Game.objects.count()
    nfinished = Game.objects.exclude(finished_at__isnull=True).count()

    rows = (
        get_user_model()
        .objects.annotate(
            ngames=Count(
                "games",
                filter=Q(games__status__in=[Game.Status.VICTORY, Game.Status.DEFEAT]),
            ),
            nwins=Count("games", filter=Q(games__winner=Game.Winner.PLAYER)),
        )
        .filter(ngames__gte=10)
        .order_by("-nwins", "username")[:5]
    )

    players = []
    for user in rows:
        winrate = round(user.nwins / user.ngames * 100, 1)  # type: ignore
        user.winrate = winrate  # type: ignore
        players.append(user)

    return {
        "nusers": nusers,
        "ngames": ngames,
        "nfinished": nfinished,
        "highscores": players,
    }
