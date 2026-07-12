import json
import random
from collections import Counter

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from app.apps.game.models import Cell, Game, Ship, Turn
from app.config.settings import FLEET, SIZE


# Главная страница.
def index(request: HttpRequest):
    return render(request, "game/base.html", _context())


# Таблица лидеров.
def leaderboard(request: HttpRequest):
    return render(
        request,
        "game/leaderboard.html",
        _context({"players": _highscores(limit=None)}),
    )


# История игр пользователя.
@login_required
def history(request: HttpRequest):
    games = (
        Game.objects.filter(player=request.user)
        .prefetch_related("turns")
        .order_by("-started_at")
    )
    total = games.count()
    nwins = games.filter(winner=Game.Winner.PLAYER).count()
    losses = games.filter(winner=Game.Winner.COMPUTER).count()
    winrate = round(nwins / total * 100, 1) if total else 0

    return render(
        request,
        "game/history.html",
        _context(
            {
                "games": games,
                "stats": {
                    "total": total,
                    "nwins": nwins,
                    "losses": losses,
                    "winrate": winrate,
                },
            }
        ),
    )


# Создание новой игры и расстановка кораблей.
@login_required
def new(request: HttpRequest):
    context = _context({"fleet": FLEET, "size": range(SIZE)})

    if request.method == "GET":
        return render(request, "game/new.html", context)

    ships, error = _ships(request.POST.get("ships", ""))
    if error:
        messages.error(request, error)
        return render(request, "game/new.html", context)

    if not ships:
        messages.error(request, "No ships.")
        return render(request, "game/new.html", context)

    with transaction.atomic():
        game = Game.objects.create(player=request.user, status=Game.Status.FIGHT)
        _grid(game, Ship.Owner.PLAYER)
        _grid(game, Ship.Owner.COMPUTER)
        _deploy(game, Ship.Owner.PLAYER, ships)
        _deploy(game, Ship.Owner.COMPUTER, _spawn())

    return redirect("game_detail", pk=game.pk)


# Просмотр текущей игры.
@login_required
def game_detail(request: HttpRequest, pk: int):
    game = get_object_or_404(Game, pk=pk, player=request.user)
    player_cells = _rows(game, Ship.Owner.PLAYER)
    bot_cells = _rows(game, Ship.Owner.COMPUTER)
    player_moves = game.turns.filter(owner=Turn.Owner.PLAYER).order_by("-created_at")  # type: ignore
    bot_moves = game.turns.filter(owner=Turn.Owner.COMPUTER).order_by("-created_at")  # type: ignore
    return render(
        request,
        "game/new.html",
        _context(
            {
                "game": game,
                "player_board": player_cells,
                "bot_board": bot_cells,
                "player_moves": player_moves[:20],
                "bot_moves": bot_moves[:20],
                "size": range(SIZE),
            }
        ),
    )


# Обработка выстрела игрока.
@login_required
@require_POST
def shoot(request: HttpRequest, pk: int):
    game = get_object_or_404(Game, pk=pk, player=request.user)

    if game.status not in [Game.Status.FIGHT, Game.Status.PLACEMENT]:
        messages.info(request, "This game is already finished.")
        return redirect("game_detail", pk=game.pk)

    try:
        x = int(request.POST["x"])
        y = int(request.POST["y"])
    except (KeyError, ValueError):
        messages.error(request, "Invalid shot coordinates.")
        return redirect("game_detail", pk=game.pk)

    if not _inside(x, y):
        messages.error(request, "Coordinates must be inside the 10x10 board.")
        return redirect("game_detail", pk=game.pk)

    target = Cell.objects.get(game=game, owner=Ship.Owner.COMPUTER, x=x, y=y)
    if target.is_hit:
        messages.warning(request, "This cell was already fired at.")
        return redirect("game_detail", pk=game.pk)

    result = _fire(game, Turn.Owner.PLAYER, target)

    if _defeated(game, Cell.Owner.COMPUTER):
        game.finish(Game.Winner.PLAYER)
        messages.success(request, "Game over. You win.")
        return redirect("game_detail", pk=game.pk)

    if result == Turn.Result.MISS:
        _boturn(request, game)
    else:
        messages.info(request, "Hit. Shoot again.")

    return redirect("game_detail", pk=game.pk)


# Собирает общий контекст для всех страниц.
def _context(extra: dict | None = None) -> dict:
    nusers = get_user_model().objects.count()
    ngames = Game.objects.count()
    nfinished = Game.objects.exclude(finished_at__isnull=True).count()
    context = {
        "nusers": nusers,
        "ngames": ngames,
        "nfinished": nfinished,
        "highscores": _highscores(limit=5),
    }
    if extra:
        context.update(extra)
    return context


# Рейтинг игроков по проценту побед.
def _highscores(limit: int | None = 10) -> list:
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
    )

    players = []

    for user in rows:
        winrate = round(user.nwins / user.ngames * 100, 1)  # type: ignore
        user.winrate = winrate  # type: ignore
        players.append(user)

    players.sort(key=lambda player: (-player.winrate, -player.nwins, player.username))
    return players if limit is None else players[:limit]


# Поле в виде матрицы клеток.
def _rows(game: Game, owner: Ship.Owner) -> list[list[Cell]]:
    cells = {
        (cell.x, cell.y): cell
        for cell in Cell.objects.filter(game=game, owner=owner).select_related("ship")
    }
    return [[cells[(x, y)] for x in range(SIZE)] for y in range(SIZE)]


# Парсинг кораблей из формы.
def _ships(s: str | bytes | bytearray) -> tuple[list[dict] | None, str | None]:
    try:
        ships = json.loads(s)
    except json.JSONDecodeError:
        return None, "No ships placed."

    if not isinstance(ships, list):
        return None, "Unknown ships format."

    normalized = []

    for ship in ships:
        if not isinstance(ship, dict):
            return None, "Unknown ship format."

        try:
            length = int(ship["length"])
            start_x = int(ship["x"])
            start_y = int(ship["y"])
        except Exception:
            return None, "Unknown ship format."

        orientation = ship.get("orientation")
        if orientation not in Ship.Orientation.values:
            return None, "Unknown ship orientation."

        normalized.append(
            {
                "length": length,
                "x": start_x,
                "y": start_y,
                "orientation": orientation,
            }
        )

    error = _validate(normalized, True)
    if error:
        return None, error

    return normalized, None


# Проверка флота по правилам.
def _validate(ships: list[dict], full: bool = False) -> str | None:
    lengths = [ship["length"] for ship in ships]

    if full and sorted(lengths) != sorted(FLEET):
        return f"Required fleet: {','.join(str(s) for s in FLEET)}."

    for s in set(FLEET):
        if FLEET.count(s) < lengths.count(s):
            return "Invalid ships amount."

    occupied = set()
    blocked = set()

    for ship in ships:
        coords = _coords(ship)

        if any(not _inside(x, y) for x, y in coords):
            return "Ships must stay inside the board."

        if occupied.intersection(coords):
            return "Ships cannot overlap."

        if blocked.intersection(coords):
            return "Ships need one free cell between them."

        occupied.update(coords)
        for x, y in coords:
            blocked.update(_neighbors(x, y))

    return None


# Создаёт пустое поле из клеток.
def _grid(game: Game, owner: Ship.Owner) -> None:
    Cell.objects.bulk_create(
        [
            Cell(game=game, owner=owner, x=x, y=y)
            for y in range(SIZE)
            for x in range(SIZE)
        ]
    )


# Расставляет корабли на поле.
def _deploy(game: Game, owner: Ship.Owner, ships: list[dict]) -> None:
    for ship_data in ships:
        ship = Ship.objects.create(
            game=game,
            owner=owner,
            length=ship_data["length"],
            start_x=ship_data["x"],
            start_y=ship_data["y"],
            orientation=ship_data["orientation"],
        )

        for x, y in _coords(ship_data):
            Cell.objects.filter(game=game, owner=owner, x=x, y=y).update(
                has_ship=True,
                ship=ship,
            )


# Случайная расстановка флота.
def _spawn() -> list[dict]:
    ships = []
    attempts = 0

    while Counter(ship["length"] for ship in ships) != Counter(FLEET):
        attempts += 1
        if attempts > 5000:
            ships = []
            attempts = 0

        length = _missing(ships)
        ship = {
            "length": length,
            "x": random.randrange(SIZE),
            "y": random.randrange(SIZE),
            "orientation": random.choice(Ship.Orientation.values),
        }

        if _validate([*ships, ship]) is None:
            ships.append(ship)

    return ships


# Длина следующего нужного корабля.
def _missing(ships: list[dict]) -> int:
    current = Counter(ship["length"] for ship in ships)

    for length in FLEET:
        if current[length] < FLEET.count(length):
            return length

    return FLEET[-1]


# Ход компьютера.
def _boturn(request: HttpRequest, game: Game) -> None:
    while game.status == Game.Status.FIGHT:
        target = _aim(game)

        if not target:
            return

        result = _fire(game, Turn.Owner.COMPUTER, target)

        if _defeated(game, Cell.Owner.PLAYER):
            game.finish(Game.Winner.COMPUTER)
            messages.error(request, "Game over. Computer wins.")
            return

        if result == Turn.Result.MISS:
            return


# Выстрел и запись хода.
def _fire(game: Game, shooter: Turn.Owner, target: Cell) -> str:
    target.is_hit = True

    target.save(update_fields=("is_hit",))

    result = _outcome(game, target)

    Turn.objects.create(
        game=game,
        owner=shooter,
        x=target.x,
        y=target.y,
        result=result,
    )

    return result


# Результат попадания.
def _outcome(game: Game, target: Cell) -> str:
    if not target.has_ship:
        return Turn.Result.MISS

    alive = Cell.objects.filter(
        game=game,
        ship=target.ship,
        has_ship=True,
        is_hit=False,
    ).exists()

    return Turn.Result.HIT if alive else Turn.Result.SUNK


# Выбор цели для компьютера.
def _aim(game: Game) -> Cell | None:
    hits = Cell.objects.filter(
        game=game, owner=Ship.Owner.PLAYER, is_hit=True, has_ship=True
    ).select_related("ship")

    for hit in hits:
        alive = Cell.objects.filter(
            game=game, ship=hit.ship, has_ship=True, is_hit=False
        ).exists()

        if not alive:
            continue

        candidates = []

        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            x, y = hit.x + dx, hit.y + dy

            if not _inside(x, y):
                continue

            cell = Cell.objects.filter(
                game=game, owner=Ship.Owner.PLAYER, x=x, y=y, is_hit=False
            ).first()

            if cell:
                candidates.append(cell)

        if candidates:
            return random.choice(candidates)

    return (
        Cell.objects.filter(game=game, owner=Ship.Owner.PLAYER, is_hit=False)
        .order_by("?")
        .first()
    )


# Проверка, уничтожен ли флот.
def _defeated(game: Game, owner: Cell.Owner) -> bool:
    return not Cell.objects.filter(
        game=game,
        owner=owner,
        has_ship=True,
        is_hit=False,
    ).exists()


# Координаты клеток корабля.
def _coords(ship: dict) -> list[tuple[int, int]]:
    if ship["orientation"] == Ship.Orientation.HORIZONTAL:
        return [(ship["x"] + offset, ship["y"]) for offset in range(ship["length"])]
    return [(ship["x"], ship["y"] + offset) for offset in range(ship["length"])]


# Соседние клетки с диагоналями.
def _neighbors(x: int, y: int) -> set[tuple[int, int]]:
    return {
        (x + dx, y + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if _inside(x + dx, y + dy)
    }


# Проверка границ поля.
def _inside(x: int, y: int) -> bool:
    return 0 <= x < SIZE and 0 <= y < SIZE
