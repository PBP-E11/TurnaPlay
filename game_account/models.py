import uuid
from django.db import models
from django.conf import settings

class GameAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # use project's configured user model
    game = models.ForeignKey('tournaments.Game', on_delete=models.PROTECT) # reference ke model Game di app tournaments
    ingame_name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        # constraint utk mencegah dua GameAccount yg beda punya kombinasi game dan ingame_name yg sama
        constraints = [
            models.UniqueConstraint(fields=['game', 'ingame_name'], name='unique_game_ingame_if_active', condition=models.Q(active=True))
        ]

    def __str__(self):
        return f"{self.ingame_name} ({self.game})"