from django.conf import settings
from django.db import models
from django.utils import timezone


class Game(models.Model):
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games",
    )

    started_at = models.DateTimeField(auto_now_add=True)

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Status(models.TextChoices):
        VICTORY = "VICTORY", "Victory"
        DEFEAT = "DEFEAT", "Defeat"
        FIGHT = "FIGHT", "Fight"
        PLACEMENT = "PLACEMENT", "Placement"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLACEMENT,
    )

    class Winner(models.TextChoices):
        COMPUTER = "COMPUTER", "Computer"
        PLAYER = "PLAYER", "Player"

    winner = models.CharField(
        max_length=20,
        choices=Winner.choices,
        null=True,
        blank=True,
    )

    def finish(self, winner):
        self.winner = winner

        self.status = (
            self.Status.VICTORY if winner == self.Winner.PLAYER else self.Status.DEFEAT
        )

        self.finished_at = timezone.now()

        self.save(update_fields=("winner", "status", "finished_at"))

        Result.objects.update_or_create(
            game=self,
            defaults={
                "player": self.player,
                "winner": winner,
                "status": self.status,
            },
        )

    def __str__(self):
        return f"Battle #{self.pk} - {self.player}"


class Ship(models.Model):
    class Orientation(models.TextChoices):
        HORIZONTAL = "H", "Horizontal"
        VERTICAL = "V", "Vertical"

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="ships",
    )

    class Owner(models.TextChoices):
        COMPUTER = "COMPUTER", "Computer"
        PLAYER = "PLAYER", "Player"

    owner = models.CharField(
        max_length=10,
        choices=Owner.choices,
    )

    length = models.PositiveSmallIntegerField()

    start_x = models.PositiveSmallIntegerField()
    start_y = models.PositiveSmallIntegerField()

    orientation = models.CharField(
        max_length=1,
        choices=Orientation.choices,
    )

    def coordinates(self):
        if self.orientation == self.Orientation.HORIZONTAL:
            return [
                (self.start_x + offset, self.start_y) for offset in range(self.length)
            ]
        return [(self.start_x, self.start_y + offset) for offset in range(self.length)]

    def __str__(self):
        return self.length


class Cell(models.Model):
    class Owner(models.TextChoices):
        COMPUTER = "COMPUTER", "Computer"
        PLAYER = "PLAYER", "Player"

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="cells",
    )

    owner = models.CharField(
        max_length=10,
        choices=Owner.choices,
    )

    x = models.PositiveSmallIntegerField()
    y = models.PositiveSmallIntegerField()

    has_ship = models.BooleanField(default=False)
    is_hit = models.BooleanField(default=False)

    ship = models.ForeignKey(
        Ship,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cells",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("game", "owner", "x", "y"),
                name="unique_cell_per_board",
            ),
        ]

    def __str__(self):
        return f"{self.owner} ({self.x}, {self.y})"


class Turn(models.Model):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="turns",
    )

    class Owner(models.TextChoices):
        COMPUTER = "COMPUTER", "Computer"
        PLAYER = "PLAYER", "Player"

    owner = models.CharField(
        max_length=10,
        choices=Owner.choices,
    )

    x = models.PositiveSmallIntegerField()
    y = models.PositiveSmallIntegerField()

    class Result(models.TextChoices):
        MISS = "MISS", "Miss"
        HIT = "HIT", "Hit"
        SUNK = "SUNK", "Sunk"

    result = models.CharField(
        max_length=10,
        choices=Result.choices,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("game", "owner", "x", "y"),
                name="unique_turn_per_target_cell",
            ),
        ]

    def __str__(self):
        return f"{self.owner} ({self.x}, {self.y}) - {self.result}"


class Result(models.Model):
    game = models.OneToOneField(
        Game,
        on_delete=models.CASCADE,
        related_name="result",
    )
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="results",
    )
    winner = models.CharField(
        max_length=20,
        choices=Game.Winner.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=Game.Status.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_victory(self):
        return self.winner == Game.Winner.PLAYER

    def __str__(self):
        return f"Result #{self.game.pk}: {self.status}"
