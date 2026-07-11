from django.contrib import admin

from app.apps.game.models import Cell, Game, Result, Ship, Turn


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "player", "started_at", "finished_at", "status", "winner")
    list_filter = ("status", "winner", "started_at")
    search_fields = ("player__username",)


@admin.register(Ship)
class ShipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "game",
        "owner",
        "length",
        "start_x",
        "start_y",
        "orientation",
    )
    list_filter = ("owner", "length", "orientation")


@admin.register(Cell)
class CellAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "owner", "x", "y", "has_ship", "is_hit", "ship")
    list_filter = ("owner", "has_ship", "is_hit")


@admin.register(Turn)
class TurnAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "owner", "x", "y", "result", "created_at")
    list_filter = ("owner", "result", "created_at")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "player", "winner", "status", "created_at")
    list_filter = ("winner", "status", "created_at")
