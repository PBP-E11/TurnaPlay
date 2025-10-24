import uuid
from django.db import models
from django.conf import settings
from django.db.models import Q

from tournament_registration.models import TournamentRegistration

class TournamentInvite(models.Model):
    class Status(models.TextChoices):
        PENDING = ('pending', 'Pending')
        ACCEPTED = ('accepted', 'Accepted')
        REJECTED = ('rejected', 'Rejected')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Penerima undangan (user yang diajak)
    user_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invites',
        verbose_name='Invited User',
    )

    # Tim pengundang (registrasi turnamen)
    tournament_registration = models.ForeignKey(
        TournamentRegistration,
        on_delete=models.CASCADE,
        related_name='sent_invites',
        verbose_name='Inviting Team',
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # Unique hanya saat status pending
            models.UniqueConstraint(
                fields=['user_account', 'tournament_registration'],
                name='unique_pending_invite_per_user_and_team',
                condition=Q(status='pending'),
            ),
        ]
        ordering = ['-created_at']
        verbose_name = 'Tournament Invite'
        verbose_name_plural = 'Tournament Invites'

    def __str__(self):
        team = self.tournament_registration.team_name
        return f"Invite to {self.user_account} for team {team} ({self.status})"